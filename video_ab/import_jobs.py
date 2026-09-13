"""Background video import jobs for web uploads."""

import json
import threading
import uuid
from pathlib import Path

from .config import DATA_DIR, OUTPUT_DIR
from .media import index_video
from .storage import LOCK, get, now, save

JOBS = OUTPUT_DIR / "import_jobs"
_running = set()
_guard = threading.RLock()


def _write(dest, state):
    dest.mkdir(parents=True, exist_ok=True)
    state["updated"] = now()
    (dest / "status.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def folder(ident):
    if not ident or any(c not in "0123456789abcdef" for c in ident):
        raise ValueError("Mã tác vụ không hợp lệ")
    return JOBS / ident


def start(session, camera, file_storage):
    if camera not in ["A", "B"]:
        raise ValueError("Camera không hợp lệ")
    if session["protocol"]["locked"] or session["records"]:
        raise ValueError("Tạo phiên mới để đổi video sau khi đã click / khóa")
    if not file_storage or not file_storage.filename:
        raise ValueError("Chưa chọn tệp video")

    ident = uuid.uuid4().hex
    dest = folder(ident)
    suffix = Path(file_storage.filename).suffix or ".mp4"
    temp = DATA_DIR / ("upload_" + ident + suffix)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_storage.save(temp)

    state = {
        "id": ident,
        "session_id": session["id"],
        "camera": camera,
        "filename": file_storage.filename,
        "status": "queued",
        "message": "Đã tải video lên máy chủ. Đang chờ chuẩn bị video.",
        "media_id": None,
        "error": None,
    }
    _write(dest, state)

    worker = threading.Thread(target=_run, args=(ident, temp), daemon=True)
    worker.start()
    return state


def _run(ident, temp):
    dest = folder(ident)
    state = json.loads((dest / "status.json").read_text(encoding="utf-8"))
    with _guard:
        _running.add(ident)
    try:
        state.update(status="processing", message="Đang đọc video và lập chỉ mục frame.")
        _write(dest, state)
        media = index_video(temp)
        with LOCK:
            session = get(state["session_id"])
            if session["protocol"]["locked"] or session["records"]:
                raise ValueError("Phiên đã có dữ liệu đo; hãy tạo phiên mới để đổi video")
            session["video" + state["camera"]] = media["id"]
            save(session, "import video " + state["camera"])
        state.update(
            status="done",
            message="Đã chuẩn bị xong video Camera " + state["camera"],
            media_id=media["id"],
            frame_count=len(media["frames"]),
            duration_seconds=media["last"] - media["first"],
        )
        _write(dest, state)
    except Exception as exc:
        state.update(status="failed", message="Không chuẩn bị được video", error=str(exc))
        _write(dest, state)
    finally:
        Path(temp).unlink(missing_ok=True)
        with _guard:
            _running.discard(ident)
