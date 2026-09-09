import argparse
import json
from fractions import Fraction

import av
from PIL import Image, ImageDraw

from video_ab.config import DEMO_DIR
from video_ab.media import index_video
from video_ab.services import new_session, stamp
from video_ab.storage import now, save


# Known-answer moving vehicle scene, explicitly synthetic. Each camera sees same vehicle.
def synthetic(name, fps, vfr=False):
    path = DEMO_DIR / name
    with av.open(str(path), "w") as output:
        # A 1 kHz encoder clock preserves the deliberately irregular 80/120 ms PTS
        # pattern. A nominal 10 fps clock would legitimately quantize it to CFR.
        stream = output.add_stream("mpeg4", rate=1000 if vfr else fps)
        stream.width = 640
        stream.height = 360
        stream.pix_fmt = "yuv420p"
        stream.time_base = Fraction(1, 1000)
        times = []
        time = 0
        while time < 22000:
            times.append(time)
            time += [80, 120][len(times) % 2] if vfr else round(1000 / fps)
        for i, time in enumerate(times):
            im = Image.new("RGB", (640, 360), "#b5c5b0")
            d = ImageDraw.Draw(im)
            d.rectangle((0, 120, 640, 280), fill="#45515b")
            d.line((0, 200, 640, 200), fill="white", width=3)
            for j, col in enumerate(["#e9b63b", "#44add1", "#b54846"]):
                x = 64 + (time / 1000 - j * 3) * 22
                d.rectangle((x - 40, 160 + j * 20, x, 178 + j * 20), fill=col)
                d.text((x - 35, 161 + j * 20), str(j + 1), fill="black")
            d.text((12, 20), "SYNTHETIC DEMO - NOT RESEARCH", fill="black")
            d.text((12, 45), f"{time / 1000:.3f} s", fill="black")
            f = av.VideoFrame.from_image(im)
            f.pts = time
            f.time_base = Fraction(1, 1000)
            for packet in stream.encode(f):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
    return index_video(path)


def main():
    parser = argparse.ArgumentParser(description="Tạo dữ liệu demo tổng hợp an toàn")
    parser.add_argument(
        "--include-public",
        action="store_true",
        help="Thêm video công khai nếu demo/street_traffic.webm đã có",
    )
    args = parser.parse_args()
    (DEMO_DIR).mkdir(parents=True, exist_ok=True)
    a = synthetic("synthetic_A.mp4", 10)
    b = synthetic("synthetic_B.mp4", 20)
    vfr = synthetic("synthetic_VFR.mp4", 10, True)
    s = new_session("Demo")
    s.update(
        site="SYNTHETIC_KNOWN_ANSWER",
        observer="Synthetic generator",
        L=100,
        uL=0.1,
        uT=0.05,
        start=0,
        end=20,
        videoA=a["id"],
        videoB=b["id"],
        lines={"A": [[0.1, 0.3], [0.1, 0.85]], "B": [[0.444, 0.3], [0.444, 0.85]]},
        line_locked={"A": True, "B": True},
    )
    s["sync"].update(
        verified=True,
        anchor_end=22,
        references=[{"source": "Synthetic common clock", "raw_A": 0, "raw_B": 0}],
        observed_offset_delta=[-0.02, 0.02],
    )
    s["protocol"].update(iid_ci=True, bootstrap=1000)
    s["sources"] = [
        dict(
            title="Synthetic moving vehicles",
            url=None,
            author="Generated for software tests",
            license="CC0",
            accessed="2026-09-06",
            segment="0–22 s; interval 0–20 s; 2 s buffer",
            assumptions="L=100 m giả định; hình ảnh minh họa, không hiện trường",
        )
    ]
    for i, (ta, tb, cls) in enumerate(
        [
            (1, 11, "MC"),
            (4, 14, "Car"),
            (7, 17, "MC"),
            (10, 19, "Car"),
            (12, 20, "MC"),
            (19, 21, "Truck"),
        ]
    ):
        r = dict(
            id=f"TEST{i + 1:03}",
            type=cls,
            direction="A→B",
            observer="Synthetic generator",
            protocol_version=s["protocol"]["version"],
            sampling_status="census",
            matching="confirmed",
            qc=[0],
            decision="keep",
            reviewer="Synthetic test",
            reason="Known-answer fixture, not observed",
            created=now(),
            updated=now(),
            description="Synthetic test vector",
        )
        stamp(
            s, r, "A", min(range(len(a["frames"])), key=lambda j: abs(a["frames"][j]["time"] - ta))
        )
        stamp(
            s, r, "B", min(range(len(b["frames"])), key=lambda j: abs(b["frames"][j]["time"] - tb))
        )
        s["records"].append(r)
    s["flow"] = [
        dict(
            id="F" + c,
            direction="A→B",
            section="A",
            interval=0,
            type=c,
            count=n,
            source="Synthetic known-answer",
            observer="Synthetic generator",
        )
        for c, n in [("MC", 8), ("Car", 4), ("Truck", 1)]
    ]
    save(s, "synthetic fixtures")
    (DEMO_DIR / "synthetic_session_id.txt").write_text(s["id"], encoding="utf-8")
    sources = list(s["sources"])
    public_id = None
    public_frames = None
    public_path = DEMO_DIR / "street_traffic.webm"
    if args.include_public:
        if not public_path.exists():
            raise FileNotFoundError("Thiếu demo/street_traffic.webm")
        public = index_video(public_path)
        p = new_session("Demo")
        p.update(
            site="PUBLIC_VIDEO_PRACTICE",
            observer="",
            L=100,
            end=public["last"],
            videoA=public["id"],
            videoB=public["id"],
        )
        p["sync"].update(
            verified=True,
            anchor_end=public["last"],
            references=[
                {"source": "Same video displayed twice; simulated cameras", "raw_A": 0, "raw_B": 0}
            ],
        )
        p["sources"] = [
            dict(
                title="Street traffic",
                url="https://commons.wikimedia.org/wiki/File:Street_traffic.webm",
                author="Editor https://www.youtube.com/user/Editor",
                license="CC BY 3.0 https://creativecommons.org/licenses/by/3.0/",
                accessed="2026-09-06",
                segment=f"0–{public['last']:.3f} s",
                assumptions="Một video hiển thị hai lần, mô phỏng camera A/B; L=100 m giả định; chưa chọn hai mặt cắt; không lặp video",
                license_verification="Commons reviewer McZusatz verified 2013-02-03; page accessed 2026-09-06",
                original="https://www.youtube.com/watch?v=_7sCYyxw4Ic",
                changes="Không sửa video; giải mã JPEG để thao tác",
            )
        ]
        save(p, "public video demo")
        (DEMO_DIR / "public_session_id.txt").write_text(p["id"], encoding="utf-8")
        sources.extend(p["sources"])
        public_id = p["id"]
        public_frames = len(public["frames"])
    (DEMO_DIR / "sources.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "synthetic_session": s["id"],
                "public_session": public_id,
                "public_frames": public_frames,
                "vfr": vfr["timing"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
