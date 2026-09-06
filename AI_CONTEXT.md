# AI context

## Project purpose

Công cụ Flask cục bộ để click hai video A–B, khớp cùng phương tiện và tính tốc độ hành trình phục vụ nghiên cứu an toàn người đi bộ.

## Technology stack

Python 3.12, Flask, SQLite, PyAV, NumPy/SciPy, openpyxl, python-docx, ReportLab; frontend HTML/CSS/JavaScript thuần.

## Main files

- `app.py`: API, SQLite, workflow phiên và upload.
- `core.py`: công thức, thống kê, sampling và summary.
- `media.py`: media storage, frame và PTS.
- `exports.py`, `workbook_export.py`: CSV/XLSX/DOCX/PDF/ZIP.
- `static/`: toàn bộ UI.
- `schema.sql`: database baseline.
- `tests.py`: nghiệm thu.

## Runtime data

Database và video nằm trong `AB_DATA_DIR` (`data/` mặc định). Output nằm trong `AB_OUTPUT_DIR` (`outputs/` mặc định). Các thư mục này không commit. Không có auth. Chỉ chạy localhost.

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
python app.py
```

## Known issues

Local single-process design; chưa có auth, migration framework, CI hoặc block bootstrap; chưa stress-test video nhiều giờ.

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
