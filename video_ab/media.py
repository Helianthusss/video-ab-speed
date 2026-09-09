import hashlib
import io
import json
import shutil
from functools import lru_cache
from pathlib import Path

import av

from .config import DATA_DIR

MEDIA = DATA_DIR / "media"


def index_video(path):
    path = Path(path).resolve()
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    key = h.hexdigest()
    out = MEDIA / key
    out.mkdir(parents=True, exist_ok=True)
    # The folder name is the content hash, so any file already stored here is the
    # same video. Reuse it instead of copying again under a new upload name.
    dest = next((f for f in sorted(out.iterdir()) if f.name != "index.json"), out / path.name)
    if not dest.exists():
        shutil.copyfile(path, dest)
    if (out / "index.json").exists():
        return json.loads((out / "index.json").read_text(encoding="utf-8"))
    with av.open(str(dest)) as c:
        st = c.streams.video[0]
        frames = []
        for i, f in enumerate(c.decode(st)):
            if f.pts is None:
                raise ValueError("Video thiếu PTS; không thể dùng đo chính xác")
            frames.append(
                {
                    "index": i,
                    "pts": f.pts,
                    "time_base": str(f.time_base),
                    "time": float(f.pts * f.time_base),
                }
            )
        if len(frames) < 2 or any(b["time"] <= a["time"] for a, b in zip(frames, frames[1:])):
            raise ValueError("PTS không tăng nghiêm ngặt")
        gaps = [b["time"] - a["time"] for a, b in zip(frames, frames[1:])]
        meta = dict(
            id=key,
            path=str(dest),
            name=path.name,
            width=st.width,
            height=st.height,
            fps=str(st.average_rate),
            time_base=str(st.time_base),
            timing="VFR" if max(gaps) - min(gaps) > 1e-5 else "CFR",
            frames=frames,
            first=frames[0]["time"],
            last=frames[-1]["time"],
        )
    (out / "index.json").write_text(json.dumps(meta), encoding="utf-8")
    return meta


def metadata(key):
    meta = json.loads((MEDIA / key / "index.json").read_text(encoding="utf-8"))
    # Resolve from the current storage root so a backup remains usable after
    # moving the project to another directory or machine.
    stored = Path(meta.get("path", "")).name
    candidate = MEDIA / key / stored
    if not candidate.exists():
        files = sorted(f for f in (MEDIA / key).iterdir() if f.name != "index.json")
        if not files:
            raise ValueError("Không xác định được file video trong kho media")
        # Content-addressed folder: any remaining file here is the same video.
        candidate = files[0]
    meta["path"] = str(candidate.resolve())
    return meta


@lru_cache(maxsize=256)
def frame_bytes(key, index):
    m = metadata(key)
    target = m["frames"][index]
    with av.open(m["path"]) as c:
        st = c.streams.video[0]
        c.seek(target["pts"], stream=st, backward=True, any_frame=False)
        for f in c.decode(st):
            if float(f.pts * f.time_base) == target["time"]:
                image = f.to_image()
                image.thumbnail((1280, 720))
                b = io.BytesIO()
                image.save(b, "JPEG", quality=90)
                return b.getvalue()
    raise ValueError("Không giải mã được khung hình có PTS yêu cầu")
