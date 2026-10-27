"""YOLO inference jobs on the host computer, isolated from survey measurements."""

import hashlib
import json
import math
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from .config import OUTPUT_DIR, ROOT
from .media import metadata

LOCK = threading.Lock()
JOBS = OUTPUT_DIR / "yolo"


def write(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    # Windows refuses the rename while another process holds the destination
    # open, and the progress endpoint reads status.json on every poll.
    for attempt in range(20):
        try:
            tmp.replace(path)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.05)


def folder(ident):
    if len(ident) != 32 or any(c not in "0123456789abcdef" for c in ident):
        raise ValueError("Mã tác vụ không hợp lệ")
    return JOBS / ident


def start(session, data):
    camera = data.get("camera", "A")
    if camera not in ("A", "B") or not session.get("video" + camera):
        raise ValueError("Chọn camera đã nhập video")
    begin = float(data.get("start", 0))
    raw_duration = data.get("duration", 0 if data.get("full") else 5)
    duration = float(raw_duration)
    confidence = float(data.get("confidence", 0.25))
    stride = int(data.get("stride", 5))
    if (
        not all(math.isfinite(v) for v in (begin, duration, confidence))
        or begin < 0
        or duration < 0
        or not 0.05 <= confidence <= 0.95
        or not (1 <= stride <= 25)
    ):
        raise ValueError("Thời điểm bắt đầu, thời lượng, tốc độ AI hoặc độ chắc của AI không hợp lệ")
    m = metadata(session["video" + camera])
    if duration == 0 or data.get("full"):
        chosen = [f for f in m["frames"] if f["time"] >= begin]
        if chosen:
            duration = max(0.0, chosen[-1]["time"] - begin)
    else:
        chosen = [f for f in m["frames"] if begin <= f["time"] < begin + duration]
    if stride > 1:
        chosen = chosen[::stride]
    if not chosen:
        raise ValueError("Không có hình video trong đoạn cần AI nhận diện")
    default_weights = ROOT / "models/yolo11n.pt" if (ROOT / "models/yolo11n.pt").is_file() else ROOT / "models/yolo26n.pt"
    weights = Path(os.environ.get("AB_YOLO_WEIGHTS", default_weights)).resolve()
    if not weights.is_file():
        raise ValueError("Chưa có weights YOLO trên máy chủ")

    weight_stat = weights.stat()
    cache_input = dict(
        crossing_method="bottom-center-v2",
        session_id=session["id"],
        media_id=m["id"],
        camera=camera,
        frames=[f["index"] for f in chosen],
        confidence=confidence,
        stride=stride,
        roi=bool(data.get("roi", True)),
        lines=session.get("lines") or {},
        distance=session.get("L"),
        weights=str(weights),
        weight_size=weight_stat.st_size,
        weight_mtime_ns=weight_stat.st_mtime_ns,
        device=os.environ.get("AB_YOLO_DEVICE", "auto"),
    )
    cache_key = hashlib.sha256(json.dumps(cache_input, sort_keys=True).encode("utf-8")).hexdigest()

    # Fast cache lookup: reuse completed inference for identical video & settings
    if JOBS.is_dir():
        for job_dir in JOBS.iterdir():
            if not job_dir.is_dir():
                continue
            status_file = job_dir / "status.json"
            detections_file = job_dir / "detections.json"
            if status_file.is_file() and detections_file.is_file():
                try:
                    cached = json.loads(status_file.read_text(encoding="utf-8"))
                    if (
                        cached.get("status") == "done"
                        and cached.get("cache_key") == cache_key
                    ):
                        return cached
                except Exception:
                    continue

    if not LOCK.acquire(blocking=False):
        raise ValueError("Đang có tác vụ YOLO chạy; hãy đợi hoàn tất")
    ident = uuid.uuid4().hex
    dest = folder(ident)
    try:
        dest.mkdir(parents=True)
        state = dict(
            id=ident,
            session_id=session["id"],
            camera=camera,
            media_id=m["id"],
            start=begin,
            duration=duration,
            confidence=confidence,
            stride=stride,
            cache_key=cache_key,
            total=len(chosen),
            processed=0,
            status="queued",
        )
        write(dest / "status.json", state)
        write(
            dest / "input.json",
            dict(
                weights=str(weights),
                media=m,
                device=os.environ.get("AB_YOLO_DEVICE", "auto"),
                # Both lines and the distance come from the session so the worker can
                # report a travel time between them; without them it only detects.
                lines=session.get("lines") or {},
                distance=session.get("L"),
                stride=stride,
                selected_indices=[f["index"] for f in chosen],
                roi=bool(data.get("roi", True)),
            ),
        )
        threading.Thread(target=launch, args=(dest,), daemon=True).start()
        return state
    except Exception:
        LOCK.release()
        raise


def launch(dest):
    try:
        with (dest / "worker.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(
                [sys.executable, "-m", "video_ab.yolo_worker", str(dest)],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=1800,
            )
        state = json.loads((dest / "status.json").read_text(encoding="utf-8"))
        if result.returncode or state["status"] not in ("done", "failed"):
            raise RuntimeError("Tiến trình YOLO dừng; xem worker.log")
    except Exception as exc:
        state = json.loads((dest / "status.json").read_text(encoding="utf-8"))
        state.update(status="failed", error=str(exc))
        write(dest / "status.json", state)
    finally:
        LOCK.release()
