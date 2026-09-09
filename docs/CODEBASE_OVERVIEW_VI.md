# Cấu trúc Python/Flask sau chuẩn hóa

```text
video_ab_github/
├── video_ab/                 Package ứng dụng
│   ├── __init__.py
│   ├── __main__.py           python -m video_ab
│   ├── config.py             Đường dẫn và biến môi trường
│   ├── web.py                Flask, API, kiểm soát truy cập
│   ├── services.py           Phiên, kiểm tra điều kiện đo, ghi mốc
│   ├── storage.py            SQLite, giao dịch, lịch sử
│   ├── core.py               Công thức, thống kê, sampling
│   ├── media.py              Video, SHA-256, PTS, frame
│   ├── exports.py            CSV, Word, PDF, ZIP
│   ├── workbook_export.py    Excel
│   ├── schema.sql
│   └── static/               HTML, CSS, JavaScript
├── scripts/                  init_db.py, demo_build.py
├── tests/                    Test nghiệm thu và tích hợp
├── docs/                     Tài liệu
├── pyproject.toml            Metadata package, CLI, Ruff
├── requirements.txt          Phiên bản thư viện runtime
├── app.py                    Entry point tương thích
├── demo_build.py             Entry point demo tương thích
├── tests.py                  Entry point test tương thích
├── Start.bat                 Launcher Windows
├── Start.command             Launcher macOS hiện có
├── .venv/                    Môi trường riêng, không commit
├── data/                     Database và video, không commit
├── demo/                     Demo người dùng, không commit
├── outputs/                  Báo cáo, không commit
└── backups/                  Backup cục bộ, không commit
```

Đây là package Python/Flask, chưa dùng PyTorch. Package ở thư mục gốc cho phép chạy trực tiếp từ checkout, không bắt buộc cài editable. Cài `python -m pip install -e ".[dev]"` khi phát triển để có CLI `video-ab` và Ruff.

## Luồng xử lý

Giao diện gọi `web.py`; API dùng `services.py` kiểm tra phiên và mốc đo, `storage.py` đọc/ghi SQLite, `media.py` xử lý video và `core.py` tính toán. Export dùng lại kết quả tính và metadata video. Mọi đường dẫn runtime tập trung ở `config.py`.

`data/`, `demo/`, `outputs/` mặc định vẫn ở gốc checkout. Giao diện và schema thuộc package. Dùng `AB_DATA_DIR`, `AB_OUTPUT_DIR`, `AB_DEMO_DIR` để chọn nơi lưu khác; nên dùng đường dẫn tuyệt đối khi chạy từ thư mục khác hoặc cài wheel.

SQLite tự đóng kết nối sau commit/rollback để giải phóng file trên Windows. Import package không tự tạo database hoặc kho media. Công thức, schema phiên và URL API giữ nguyên. Các module dùng import rõ ràng, không còn `import *`; mã được định dạng bằng Ruff.

## Lệnh phát triển

```powershell
.\.venv\Scripts\python.exe -X utf8 -m video_ab
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pip check
```

Test chạy trong process Python mới, cấu hình đường dẫn tạm trước khi import ứng dụng; tự tạo và dọn database/video tổng hợp. Không cần tạo demo trước và không ghi đè `demo/` của người dùng. Lệnh cũ `python app.py`, `python demo_build.py`, `python tests.py` vẫn dùng được.

## Xác minh ngày 08/09/2026

Python 3.12.14 trên Windows: 31 test đạt (26 test cũ và kiểm tra tài nguyên giao diện, đường dẫn tạm, xuất báo cáo, đóng SQLite, tải backup). Ruff đạt. Cài package editable thành công.

Git checkpoint trước refactor: `04e75fcbb53a42a9e183eee0aa0a5cb6b7b03f50`, chứa thay đổi tracked trước khi tổ chức lại; không chứa dữ liệu runtime hoặc file untracked. Môi trường macOS cũ được giữ ở `backups/venv-macos-20260908/`.
