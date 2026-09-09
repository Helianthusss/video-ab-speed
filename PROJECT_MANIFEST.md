# Project manifest

## Mục đích

Công cụ click video đo tốc độ hành trình từng phương tiện giữa hai camera/mặt cắt A–B trong khảo sát an toàn người đi bộ. Ứng dụng tách đếm lưu lượng khỏi mẫu tốc độ, giữ PTS/frame gốc, hiệu chỉnh đồng bộ, QC, sampling, reliability và truy vết kết quả.

## Technology stack

| Thành phần | Công nghệ |
|---|---|
| Runtime | Python 3.12 |
| Backend | Flask 3.1 |
| Frontend | HTML, CSS, JavaScript thuần |
| Database | SQLite |
| Video | PyAV |
| Thống kê | NumPy, SciPy |
| Excel | openpyxl |
| Word/PDF | python-docx, ReportLab |

Không có framework frontend, package manager Node hoặc bước build frontend. Có Basic Auth trong web.py; không có cloud service hay API bên thứ ba.

## Entry points và cấu trúc

- `python -m video_ab`: server, mặc định 127.0.0.1:8765.
- `app.py`: entry point tương thích và WSGI `app:app`.
- `Start.bat`: Windows; `Start.command`: launcher macOS hiện có.
- `python -m scripts.demo_build`: dữ liệu tổng hợp, hỗ trợ AB_DEMO_DIR.
- `python scripts/init_db.py`: dựng database từ video_ab/schema.sql.
- `python -m unittest discover -s tests -v`: tự tạo/dọn dữ liệu test riêng.

Package `video_ab/` tách config, web, services, storage, core, media, exports và workbook_export; chứa static và schema.sql. Xem [sơ đồ đầy đủ](docs/CODEBASE_OVERVIEW_VI.md). Metadata và cấu hình Ruff trong pyproject.toml.

## Database

File mặc định: `data/survey.sqlite`; có thể đổi thư mục bằng `AB_DATA_DIR`.

| Bảng | Vai trò |
|---|---|
| `sessions` | một JSON snapshot đầy đủ cho mỗi phiên |
| `history` | snapshot sau mỗi thao tác để undo/redo và phục hồi |
| `sqlite_sequence` | SQLite quản lý sequence của history |

Không có migration framework. `video_ab/schema.sql` là baseline schema. `video_ab/storage.py` tự tạo bảng để giữ backward compatibility. Database runtime không được commit.

## Storage

Video A/B upload được băm SHA-256 và sao chép vào `data/media/<hash>/`. `index.json` giữ metadata, frame index, PTS và time base. Session JSON lưu video ID/hash; đường dẫn thật được giải quyết từ `AB_DATA_DIR` khi đọc để backup có thể di chuyển.

Ứng dụng chưa hỗ trợ upload hồ sơ PDF/Word/Excel tổng quát. Snapshot JSON có thể upload để tạo một phiên mới. Output sinh trong `AB_OUTPUT_DIR`.

## API chính

- `GET /`: giao diện.
- `GET /api/sessions`, `GET /api/session/<id>`, `POST /api/new`.
- `POST /api/import/<session>/<A|B>`: upload video.
- `GET /api/media/<id>`, `GET /api/frame/<id>/<index>`.
- `POST /api/action/<session>`: settings, lines, click, matching, flow, sampling, logs và audit.
- `GET /api/summary/<session>`.
- `GET /api/history/<session>`, `POST /api/restore/<session>/<seq>`.
- `GET /api/export/<session>`, `GET /api/backup`, `POST /api/restore_file`.

Ứng dụng kiểm tra Host/Origin; host ngoài localhost phải khớp AB_ALLOWED_HOST và dùng Basic Auth (AB_USERNAME / AB_PASSWORD).

## Quy tắc kiến trúc cần giữ

- Không ghi đè timestamp gốc; áp dụng correction khi tính.
- Không dùng trị tuyệt đối cho thời gian hai hướng.
- Không dùng số xe khớp làm lưu lượng.
- QC flag tách khỏi quyết định giữ/loại; không xóa dữ liệu gốc bị loại.
- Demo và Research phải tách biệt và có nhãn rõ.
- Không gộp Mean toàn dòng từ sampling không tỷ lệ nếu chưa có trọng số hợp lệ.
- Giữ đúng thứ tự cột V4 ở đầu bảng Raw và Site summary.
- Không đổi SQLite hoặc storage architecture trong patch nhỏ.

## Không commit

- `.env` và mọi credential.
- `data/`, `*.sqlite*` và database thật.
- `media/`, `uploads/`, `storage/`, video khảo sát và file người dùng.
- `outputs/`, báo cáo sinh tự động và archive ZIP.
- `.venv/`, `vendor/`, `node_modules/`, cache và log.
- Backup nguyên trạng của dự án.

## Chạy

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/init_db.py
python app.py
```

## Vấn đề kỹ thuật còn tồn tại

- Flask development server chỉ phù hợp local development.
- Basic Auth đã có; vẫn cần thiết kế HTTPS và triển khai phù hợp nếu phục vụ ngoài máy cá nhân.
- SQLite/local media phù hợp một process. Multi-instance cần database và object storage dùng chung.
- Lập chỉ mục toàn bộ frame có thể tốn thời gian/dung lượng với video nhiều giờ; chưa stress-test quy mô đó.
- Block bootstrap chưa được triển khai.
- Audit blinding là che trong UI, không phải phân quyền bảo mật.
- Chưa có migration versioning ngoài `video_ab/schema.sql` baseline.
- Chưa có CI workflow; chạy `tests.py` trước mỗi release.
