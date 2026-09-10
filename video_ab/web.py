"""Flask routes and request access controls."""

import copy
import hashlib
import hmac
import io
import json
import math
import os
import random
import sqlite3
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, jsonify, redirect, request, send_file, send_from_directory

from .config import AUTH_PASSWORD, AUTH_USERNAME, DATA_DIR, PACKAGE_DIR
from .core import CLASSES, measure, plan, summary
from .media import frame_bytes, index_video, metadata
from .services import measurement_readiness, new_session, stamp, validate_session
from .storage import LOCK, db, get, now, save

app = Flask(__name__, static_folder=str(PACKAGE_DIR / "static"), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024**3


@app.errorhandler(Exception)
def error(e):
    return jsonify(error=str(e)), 400


@app.before_request
def local_only():
    host = request.host.split(":", 1)[0].lower()

    if host in ["127.0.0.1", "localhost"]:
        if request.method == "POST":
            origin = request.headers.get("Origin")
            if origin and urlsplit(origin).hostname not in ["127.0.0.1", "localhost"]:
                raise ValueError("Nguồn yêu cầu không hợp lệ")
        return None

    allowed_host = os.environ.get("AB_ALLOWED_HOST", "").strip().lower()
    if not allowed_host or host != allowed_host:
        raise ValueError("Host không được phép")

    if request.method == "POST":
        origin = request.headers.get("Origin")
        if origin and urlsplit(origin).hostname != allowed_host:
            raise ValueError("Nguồn yêu cầu không hợp lệ")


# In-app browsers inside chat applications often refuse to render the Basic Auth
# dialog, so a plain login form is offered alongside it. Both grant the same access.
LOGIN_COOKIE = "ab_auth"
LOGIN_HTML = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Đăng nhập · Khảo sát tốc độ A–B</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:#f3f6f8;color:#173043;font:16px/1.45 system-ui,-apple-system,sans-serif}
form{background:#fff;padding:28px 24px;border-radius:12px;width:min(360px,92vw);
box-shadow:0 2px 18px rgba(18,50,68,.14)}
small{letter-spacing:2px;font-size:11px;font-weight:750;color:#14777b}
h1{font-size:20px;margin:6px 0 18px}
label{display:block;margin-bottom:14px;font-size:14px}
input{width:100%;padding:11px;margin-top:5px;border:1px solid #d5e0e5;
border-radius:7px;font-size:16px;background:#fff;color:#173043}
button{width:100%;padding:12px;border:0;border-radius:7px;background:#14777b;
color:#fff;font-size:16px;font-weight:600}
.err{background:#fdecea;color:#ad3e28;padding:10px;border-radius:7px;
margin:0 0 14px;font-size:14px}
</style></head><body>
<form method="post" action="/login">
<small>NGHIÊN CỨU AN TOÀN NGƯỜI ĐI BỘ</small>
<h1>Khảo sát tốc độ A–B</h1>
<!--error-->
<label>Tên đăng nhập<input name="username" autocomplete="username"
autocapitalize="off" autocorrect="off" required></label>
<label>Mật khẩu<input name="password" type="password"
autocomplete="current-password" required></label>
<button type="submit">Đăng nhập</button>
</form></body></html>
"""


def login_token():
    """Stateless cookie value; changes whenever the configured credentials change."""
    secret = "ab-login-v1:" + AUTH_USERNAME + ":" + AUTH_PASSWORD
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def credentials_match(username, password):
    return hmac.compare_digest(username or "", AUTH_USERNAME) and hmac.compare_digest(
        password or "", AUTH_PASSWORD
    )


def login_page(error=""):
    body = LOGIN_HTML.replace("<!--error-->", '<p class="err">' + error + "</p>" if error else "")
    return body, 401 if error else 200, {"Content-Type": "text/html; charset=utf-8"}


@app.before_request
def require_auth():
    host = request.host.split(":")[0]
    if host in ["127.0.0.1", "localhost"] and not AUTH_USERNAME and not AUTH_PASSWORD:
        return None

    if not AUTH_USERNAME or not AUTH_PASSWORD:
        return "Server authentication is not configured", 503

    auth = request.authorization
    if auth and credentials_match(auth.username, auth.password):
        return None

    if hmac.compare_digest(request.cookies.get(LOGIN_COOKIE, ""), login_token()):
        return None

    if request.path == "/login":
        return None

    # A browser asking for a page gets the form; every other client keeps Basic Auth.
    if request.method == "GET" and "text/html" in request.headers.get("Accept", ""):
        return redirect("/login")

    return (
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="Video AB Speed Survey"'},
    )


@app.get("/login")
def login_form():
    return login_page()


@app.post("/login")
def login_submit():
    if not credentials_match(request.form.get("username"), request.form.get("password")):
        return login_page("Sai tên đăng nhập hoặc mật khẩu.")
    response = redirect("/")
    response.set_cookie(
        LOGIN_COOKIE,
        login_token(),
        max_age=12 * 3600,
        httponly=True,
        samesite="Lax",
        secure=request.headers.get("X-Forwarded-Proto", request.scheme) == "https",
    )
    return response


@app.get("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/sessions")
def sessions():
    with db() as c:
        rows = [json.loads(x[0]) for x in c.execute("SELECT body FROM sessions")]
    return jsonify(
        [
            {"id": s["id"], "site": s["site"], "mode": s["mode"], "updated": s["updated"]}
            for s in rows
        ]
    )


@app.post("/api/new")
def create():
    return jsonify(save(new_session(request.json["mode"]), "create"))


@app.get("/api/session/<sid>")
def session(sid):
    return jsonify(get(sid))


@app.get("/api/summary/<sid>")
def sums(sid):
    return jsonify(summary(get(sid)))


@app.get("/api/media/<key>")
def meta(key):
    return jsonify(metadata(key))


@app.get("/api/frame/<key>/<int:index>")
def frame(key, index):
    return send_file(io.BytesIO(frame_bytes(key, index)), mimetype="image/jpeg")


@app.get("/api/video/<key>")
def stream_video(key):
    if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
        raise ValueError("Mã video không hợp lệ")
    return send_file(metadata(key)["path"], conditional=True)


@app.post("/api/import/<sid>/<cam>")
def imp(sid, cam):
    if cam not in ["A", "B"]:
        raise ValueError("Camera không hợp lệ")
    s = get(sid)
    if s["protocol"]["locked"] or s["records"]:
        raise ValueError("Tạo phiên mới để đổi video sau khi đã click / khóa")
    f = request.files.get("file")
    if not f or not f.filename:
        raise ValueError("Chưa chọn tệp video")
    temp = DATA_DIR / ("upload_" + uuid.uuid4().hex + Path(f.filename).suffix)
    f.save(temp)
    try:
        m = index_video(temp)
    finally:
        temp.unlink(missing_ok=True)
    s["video" + cam] = m["id"]
    save(s, "import video " + cam)
    return jsonify(s)


@app.post("/api/action/<sid>")
def action(sid):
    with LOCK:
        s = get(sid)
        d = request.json
        if d.get("revision") != s["revision"]:
            raise ValueError("Phiên đã thay đổi. Tải lại trước khi lưu để tránh ghi đè.")
        op = d["op"]
        v = d.get("value", {})
        if op == "settings":
            allowed = [
                "project",
                "site",
                "location",
                "observer",
                "session_start",
                "timezone",
                "reference",
                "L",
                "uL",
                "uT",
                "start",
                "end",
                "interval_seconds",
                "setup",
                "protocol",
                "sync",
            ]
            if s["protocol"]["locked"] and any(
                k in v and v[k] != s[k]
                for k in ["protocol", "L", "start", "end", "interval_seconds", "reference"]
            ):
                raise ValueError("Protocol đã khóa. Tạo phiên mới cho thay đổi thiết kế.")
            old = copy.deepcopy(s["sync"])
            for k in allowed:
                if k in v:
                    s[k] = v[k]
            if old != s["sync"]:
                s["sync"]["version"] = old["version"] + 1
            validate_session(s)
        elif op == "line":
            cam = v["camera"]
            if cam not in ["A", "B"]:
                raise ValueError("Camera không hợp lệ")
            if s["line_locked"][cam]:
                raise ValueError("Vạch đã khóa")
            points = v.get("points")
            if (
                not isinstance(points, list)
                or len(points) != 2
                or any(
                    not isinstance(p, list)
                    or len(p) != 2
                    or any(not isinstance(x, (int, float)) or x < 0 or x > 1 for x in p)
                    for p in points
                )
            ):
                raise ValueError("Hãy chọn đủ hai điểm hợp lệ trên ảnh trước khi lưu vạch")
            s["lines"][cam] = v["points"]
            s["line_locked"][cam] = v["locked"]
        elif op == "entry":
            missing = measurement_readiness(s)
            if missing:
                raise ValueError("Chưa thể ghi mốc: " + "; ".join(missing))
            if v.get("direction") not in ["A→B", "B→A"]:
                raise ValueError("Hướng xe không hợp lệ")
            if v.get("type") not in CLASSES:
                raise ValueError("Loại xe không hợp lệ")
            if not str(v.get("description", "")).strip():
                raise ValueError("Hãy nhập đặc điểm nhận dạng xe")
            cam = "A" if v["direction"] == "A→B" else "B"
            r = dict(
                id=v.get("id") or "V" + uuid.uuid4().hex[:10],
                type=v["type"],
                direction=v["direction"],
                observer=s["observer"],
                protocol_version=s["protocol"]["version"],
                sync_version=s["sync"]["version"],
                qc=[0],
                decision="review",
                matching="pending",
                reason="",
                sampling_status=v.get("sampling_status", "census"),
                description=v.get("description", ""),
                created=now(),
                updated=now(),
            )
            if any(x["id"] == r["id"] for x in s["records"]):
                raise ValueError("Trùng ID")
            stamp(s, r, cam, v["frame"])
            s["records"].append(r)
        elif op in ["exit", "record"]:
            r = next((x for x in s["records"] if x["id"] == v.get("id")), None)
            if not r:
                raise ValueError("Không tìm thấy xe đang xử lý")
            if op == "exit":
                stamp(s, r, "B" if r["direction"] == "A→B" else "A", v["frame"])
                r["matching"] = "review"
            else:
                for k in [
                    "type",
                    "direction",
                    "qc",
                    "decision",
                    "matching",
                    "reason",
                    "reviewer",
                    "description",
                    "sampling_status",
                ]:
                    if k in v:
                        r[k] = v[k]
                for cam in ["A", "B"]:
                    if "frame" + cam in v and v["frame" + cam] is not None:
                        stamp(s, r, cam, int(v["frame" + cam]))
            if not set(r["qc"]).issubset(set(range(7))) or (0 in r["qc"] and len(r["qc"]) > 1):
                raise ValueError("QC=0 không đi với mã lỗi")
            if r["decision"] in ["keep", "exclude"] and (
                not r.get("reviewer") or not r.get("reason")
            ):
                raise ValueError("Quyết định cần người duyệt và lý do")
            r["updated"] = now()
        elif op == "flow":
            if v["count"] < 0 or int(v["count"]) != v["count"] or v["type"] not in CLASSES:
                raise ValueError("Số đếm nguyên không âm và class hợp lệ")
            v["id"] = v.get("id", uuid.uuid4().hex)
            v["source"] = "Nhập tay"
            v["observer"] = s["observer"]
            s["flow"] = [f for f in s["flow"] if f["id"] != v["id"]] + [v]
        elif op == "plan":
            p = plan(
                int(v["N"]),
                v["cv"],
                v["precision"],
                int(v["seed"]),
                v["fpc"],
                v["eligible"],
                v["rare"],
            )
            p.update(
                type=v["type"],
                direction=v["direction"],
                interval=v["interval"],
                id=uuid.uuid4().hex,
            )
            s["plans"].append(p)
        elif op == "log":
            s[v["kind"]].append(dict(v["record"], created=now(), observer=s["observer"]))
        elif op == "audit_select":
            pool = [r for r in s["records"] if r.get("tA") is not None and r.get("tB") is not None]
            rng = random.Random(v["seed"])
            n = math.ceil(len(pool) * v["fraction"])
            chosen = rng.sample(pool, n)
            for r in chosen:
                s["audits"].append(
                    dict(
                        id=uuid.uuid4().hex,
                        record_id=r["id"],
                        seed=v["seed"],
                        fraction=v["fraction"],
                        observer=v["observer"],
                        kind=v["kind"],
                        matching="uncertain",
                        status="pending",
                    )
                )
        elif op == "audit_save":
            a = next(a for a in s["audits"] if a["id"] == v["id"])
            r = next(r for r in s["records"] if r["id"] == a["record_id"])
            rep = dict(r)
            stamp(s, rep, "A", v["frameA"])
            stamp(s, rep, "B", v["frameB"])
            a.update(v, status="done", tA=rep["tA"], tB=rep["tB"], speed=measure(rep, s)["speed"])
        else:
            raise ValueError("Thao tác không hỗ trợ")
        # Duplicate matching event is flagged, never silently removed. Same-frame vehicles are allowed with review.
        for r in s["records"]:
            r["duplicate_event"] = any(
                x["id"] != r["id"]
                and x.get("frameA") == r.get("frameA")
                and x.get("frameB") == r.get("frameB")
                and r.get("frameB") is not None
                for x in s["records"]
            )
        return jsonify(save(s, op))


@app.get("/api/history/<sid>")
def history(sid):
    with db() as c:
        return jsonify(
            [
                dict(seq=r[0], at=r[1], action=r[2])
                for r in c.execute(
                    "SELECT seq,at,action FROM history WHERE session=? ORDER BY seq DESC", (sid,)
                )
            ]
        )


@app.post("/api/restore/<sid>/<int:seq>")
def restore(sid, seq):
    with db() as c:
        r = c.execute("SELECT body FROM history WHERE session=? AND seq=?", (sid, seq)).fetchone()
    if not r:
        raise ValueError("Không có phiên bản")
    s = json.loads(r[0])
    s["revision"] = get(sid)["revision"]
    return jsonify(save(s, "restore " + str(seq)))


@app.get("/api/export/<sid>")
def export(sid):
    from .exports import export_bundle

    return send_file(export_bundle(get(sid)), as_attachment=True)


@app.get("/api/backup")
def backup():
    out = DATA_DIR / "backup.sqlite"
    with db() as src:
        from contextlib import closing

        with closing(sqlite3.connect(out)) as dst:
            src.backup(dst)
    return send_file(out, as_attachment=True)


@app.post("/api/restore_file")
def restore_file():
    s = json.load(request.files["file"])
    validate_session(s)
    s["id"] = str(uuid.uuid4())
    return jsonify(save(s, "restore snapshot as new session"))


def main():
    app.run(
        host=os.environ.get("AB_HOST", "127.0.0.1"),
        port=int(os.environ.get("AB_PORT", "8765")),
        threaded=True,
    )


@app.post("/api/yolo/<sid>")
def yolo_start(sid):
    from .yolo_jobs import start

    return jsonify(start(get(sid), request.get_json() or {})), 202


@app.get("/api/yolo/job/<ident>")
def yolo_status(ident):
    from .yolo_jobs import folder

    return jsonify(json.loads((folder(ident) / "status.json").read_text(encoding="utf-8")))


@app.get("/api/yolo/job/<ident>/result")
def yolo_result(ident):
    from .yolo_jobs import folder

    dest = folder(ident)
    state = json.loads((dest / "status.json").read_text(encoding="utf-8"))
    if state["status"] != "done":
        raise ValueError("Kết quả chưa sẵn sàng")
    return send_file(dest / "detections.json", as_attachment=True)
