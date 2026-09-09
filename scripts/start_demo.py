"""Start the survey application behind a temporary public address.

Runs a Cloudflare quick tunnel, reads the address it prints, then starts the
application configured for exactly that address. Both processes stop together
when this script is interrupted.
"""

import os
import re
import secrets
import string
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
ADDRESS = re.compile(rb"https://[a-z0-9-]+\.trycloudflare\.com")
CLOUDFLARED = [
    Path(r"C:/Program Files (x86)/cloudflared/cloudflared.exe"),
    Path(r"C:/Program Files/cloudflared/cloudflared.exe"),
]


def cloudflared():
    for candidate in CLOUDFLARED:
        if candidate.exists():
            return str(candidate)
    from shutil import which

    found = which("cloudflared")
    if not found:
        raise SystemExit(
            "Không tìm thấy cloudflared.\nCài bằng lệnh: winget install --id Cloudflare.cloudflared"
        )
    return found


def banner(address, username, password):
    line = "=" * 62
    print("\n" + line)
    print("  ĐỊA CHỈ DEMO:  " + address)
    print("  Tài khoản   :  " + username)
    print("  Mật khẩu    :  " + password)
    print(line)
    print("  Gửi ba dòng trên cho người xem. Mở được trên điện thoại và máy khác.")
    print("  Giữ cửa sổ này mở. Nhấn Ctrl+C để dừng demo.")
    print(line + "\n")


def main():
    port = os.environ.get("AB_PORT", "8765")
    username = os.environ.get("AB_USERNAME") or "demo"
    password = os.environ.get("AB_PASSWORD") or "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(12)
    )

    log = Path(tempfile.gettempdir()) / "video-ab-tunnel.log"
    log.write_bytes(b"")
    print("Đang mở đường hầm ra Internet...", flush=True)
    tunnel = subprocess.Popen(
        [cloudflared(), "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"],
        stdout=log.open("wb"),
        stderr=subprocess.STDOUT,
    )

    address = None
    for _ in range(120):
        if tunnel.poll() is not None:
            raise SystemExit("cloudflared đã thoát. Xem chi tiết trong " + str(log))
        match = ADDRESS.search(log.read_bytes())
        if match:
            address = match.group().decode()
            break
        time.sleep(0.5)
    if not address:
        tunnel.terminate()
        raise SystemExit("Không lấy được địa chỉ sau 60 giây. Kiểm tra kết nối mạng.")

    environment = dict(
        os.environ,
        AB_ALLOWED_HOST=address.removeprefix("https://"),
        AB_USERNAME=username,
        AB_PASSWORD=password,
        AB_PORT=port,
    )
    application = subprocess.Popen(
        [str(PYTHON) if PYTHON.exists() else sys.executable, "-X", "utf8", "-m", "video_ab"],
        cwd=ROOT,
        env=environment,
    )
    banner(address, username, password)

    try:
        application.wait()
    except KeyboardInterrupt:
        print("\nĐang dừng demo...")
    finally:
        for process in (application, tunnel):
            if process.poll() is None:
                process.terminate()
        print("Đã dừng. Địa chỉ trên không còn truy cập được.")


if __name__ == "__main__":
    main()
