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

Không có framework frontend, package manager Node hoặc bước build frontend. Không có auth, cloud service hay API bên thứ ba.

## Entry points

- `app.py`: Flask server và API; mặc định `127.0.0.1:8765`.
- `Start.command`: launcher macOS, ưu tiên `.venv/bin/python`.
- `demo_build.py`: tạo video và dữ liệu tổng hợp an toàn.
- `scripts/init_db.py`: dựng database trống từ `schema.sql`.
- `tests.py`: kiểm thử nghiệm thu.

## Cấu trúc quan trọng

```text
.
├── app.py                 API, persistence và session workflow
├── core.py                công thức tốc độ, thống kê, sampling, summary
├── media.py               nhập video, SHA-256, frame/PTS và giải mã JPEG
├── exports.py             dữ liệu xuất, CSV, Word, PDF và ZIP
├── workbook_export.py     Excel nhiều sheet
├── static/
│   ├── index.html         giao diện tiếng Việt
│   ├── app.js             thao tác video và API client
│   └── style.css
├── schema.sql             schema SQLite tái tạo
├── scripts/init_db.py
├── demo_build.py
├── tests.py
└── docs/
```

Các thư mục runtime `data/`, `demo/` và `outputs/` được tạo khi cần và không commit.

## Database

File mặc định: `data/survey.sqlite`; có thể đổi thư mục bằng `AB_DATA_DIR`.

| Bảng | Vai trò |
|---|---|
| `sessions` | một JSON snapshot đầy đủ cho mỗi phiên |
| `history` | snapshot sau mỗi thao tác để undo/redo và phục hồi |
| `sqlite_sequence` | SQLite quản lý sequence của history |

Không có migration framework. `schema.sql` là baseline schema. `app.py` vẫn tự tạo bảng để giữ backward compatibility. Database runtime không được commit.

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

Ứng dụng chặn Host/Origin ngoài localhost. Đây không phải authentication hoặc authorization.

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
- Chưa có auth; không bind ra mạng ngoài khi chưa thiết kế bảo mật.
- SQLite/local media phù hợp một process. Multi-instance cần database và object storage dùng chung.
- Lập chỉ mục toàn bộ frame có thể tốn thời gian/dung lượng với video nhiều giờ; chưa stress-test quy mô đó.
- Block bootstrap chưa được triển khai.
- Audit blinding là che trong UI, không phải phân quyền bảo mật.
- Chưa có migration versioning ngoài `schema.sql` baseline.
- Chưa có CI workflow; chạy `tests.py` trước mỗi release.
