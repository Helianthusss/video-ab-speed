# AI context

## Project purpose

Công cụ Flask cục bộ để click hai video A–B, khớp cùng phương tiện và tính tốc độ hành trình phục vụ nghiên cứu an toàn người đi bộ.

## Technology stack

Python 3.12, Flask, SQLite, PyAV, NumPy/SciPy, openpyxl, python-docx, ReportLab; frontend HTML/CSS/JavaScript thuần.

## Main files

- `video_ab/web.py`: Flask API, upload, access controls.
- `video_ab/config.py`: đường dẫn và biến môi trường.
- `video_ab/storage.py`: SQLite và lịch sử; context manager đóng kết nối.
- `video_ab/services.py`: workflow phiên và kiểm tra mốc đo.
- `video_ab/core.py`: công thức, thống kê, sampling.
- `video_ab/media.py`: video, frame và PTS.
- `video_ab/exports.py`, `video_ab/workbook_export.py`: xuất báo cáo.
- `video_ab/static/`, `video_ab/schema.sql`: tài nguyên package.
- `scripts/`: khởi tạo DB và tạo demo; `tests/`: test dữ liệu tạm.
- `pyproject.toml`: metadata package, CLI và Ruff.
- `app.py`, `demo_build.py`, `tests.py`: entry point tương thích.

## Runtime data

Database và video nằm trong `AB_DATA_DIR` (`data/` mặc định). Output nằm trong `AB_OUTPUT_DIR` (`outputs/` mặc định). Các thư mục này không commit. Có Basic Auth cho host ngoài localhost. Demo dùng AB_DEMO_DIR; test tự cấu hình thư mục tạm trong process mới.

## Architectural rules

- Giữ timestamp/PTS gốc và correction có phiên bản.
- Tách flow count khỏi speed sample.
- Không xóa bản ghi bị loại; QC tách khỏi quyết định phân tích.
- Demo không được dùng làm kết quả Research.
- Giữ schema output và backward compatibility.

## Do not touch without explicit scope

- Không truy cập hoặc sửa database Research/production.
- Không đổi framework, database hoặc storage architecture trong patch nhỏ.
- Không đổi công thức/phương pháp nếu chưa đối chiếu `docs/METHOD_TRACEABILITY.md`.
- Không commit database, media, output, `.env` hoặc backup.

## How to run

```bash
source .venv/bin/activate
python -m video_ab
python -m unittest discover -s tests -v
```

## Known issues

Local single-process design; chưa có migration framework, CI hoặc block bootstrap; chưa stress-test video nhiều giờ.

## Rules for future AI work

1. Không đọc toàn bộ repository nếu task chỉ liên quan một module.
2. Chỉ đọc file trực tiếp liên quan.
3. Không refactor ngoài phạm vi.
4. Không thay đổi architecture khi không cần thiết.
5. Không thay dependency nếu không cần.
6. Ưu tiên patch nhỏ.
7. Giữ backward compatibility.
8. Trước thay đổi lớn phải tạo Git checkpoint/commit.
9. Sau thay đổi phải báo rõ file đã sửa.
10. Không truy cập hoặc chỉnh database production nếu task không yêu cầu.
