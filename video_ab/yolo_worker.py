import json
import os
import sys
import time
from pathlib import Path

from .yolo_jobs import write


def run(dest):
    state = json.loads((dest / "status.json").read_text(encoding="utf-8"))
    try:
        os.environ["YOLO_CONFIG_DIR"] = str(dest / "config")
        (dest / "config").mkdir(exist_ok=True)
        import av
        import torch
        from ultralytics import YOLO

        config = json.loads((dest / "input.json").read_text(encoding="utf-8"))
        torch.set_num_threads(2)
        device = config["device"]
        if device == "auto":
            device = "0" if torch.cuda.is_available() else "cpu"
        state.update(status="running", device=device)
        write(dest / "status.json", state)
        model = YOLO(config["weights"])
        ids = [
            i
            for i, name in model.names.items()
            if name in ("car", "motorcycle", "truck", "bus", "bicycle")
        ]
        if not ids:
            raise ValueError("Weights không có nhãn phương tiện COCO được hỗ trợ")
        m = config["media"]
        selected = [
            f
            for f in m["frames"]
            if state["start"] <= f["time"] < state["start"] + state["duration"]
        ]
        by_pts = {f["pts"]: f for f in selected}
        rows = []
        begun = time.monotonic()
        with av.open(m["path"]) as source:
            st = source.streams.video[0]
            source.seek(selected[0]["pts"], stream=st, backward=True)
            for frame in source.decode(st):
                if frame.pts > selected[-1]["pts"]:
                    break
                if frame.pts not in by_pts:
                    continue
                f = by_pts[frame.pts]
                result = model.predict(
                    frame.to_ndarray(format="bgr24"),
                    classes=ids,
                    conf=state["confidence"],
                    imgsz=640,
                    device=device,
                    verbose=False,
                )[0]
                boxes = [
                    dict(
                        label=model.names[int(b.cls.item())],
                        confidence=round(float(b.conf.item()), 4),
                        xyxyn=b.xyxyn[0].tolist(),
                    )
                    for b in result.boxes
                ]
                rows.append(
                    dict(
                        frame=f["index"],
                        pts=f["pts"],
                        time_base=f["time_base"],
                        time=f["time"],
                        boxes=boxes,
                    )
                )
                state["processed"] += 1
                if state["processed"] % 5 == 0:
                    write(dest / "status.json", state)
        if len(rows) != state["total"]:
            raise ValueError("Không giải mã đủ frame")
        write(
            dest / "detections.json",
            dict(
                session_id=state["session_id"],
                camera=state["camera"],
                media_id=state["media_id"],
                weights=Path(config["weights"]).name,
                frames=rows,
                note="Detection only; not unique vehicle count or cross-camera matching",
            ),
        )
        state.update(
            status="done",
            elapsed_seconds=round(time.monotonic() - begun, 2),
            detections=sum(len(r["boxes"]) for r in rows),
        )
    except Exception as exc:
        state.update(status="failed", error=str(exc))
    write(dest / "status.json", state)


if __name__ == "__main__":
    run(Path(sys.argv[1]))
