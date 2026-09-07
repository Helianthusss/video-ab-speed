# Công cụ click video đo tốc độ hai camera A B

Ứng dụng phục vụ khảo sát tốc độ hành trình phương tiện giữa hai mặt cắt A–B. Người thao tác mở hai video, chọn chính xác từng frame, khớp cùng xe, ghi QC, quản lý lưu lượng và lấy mẫu, rồi xuất CSV, Excel, Word và PDF.

## Kiến trúc

- Backend: Flask 3.1.3 trên Python.
- Frontend: HTML, CSS và JavaScript thuần trong `static/`; không có bước build frontend.
- Database: SQLite cục bộ tại `data/survey.sqlite` theo mặc định.
- Video storage: file được sao chép vào `data/media/<sha256>/`; database lưu mã SHA-256 của video trong JSON phiên khảo sát.
- Export: `outputs/<session-id>/` và gói ZIP.
- Authentication: chưa có; ứng dụng chỉ cho phép request tới localhost.

## Môi trường đã kiểm tra

- Python 3.12.14.
- SQLite 3.51.0.
- macOS. Mã nguồn dùng thư viện đa nền tảng, nhưng `Start.command` dành cho macOS.
- Node.js không còn là dependency chạy ứng dụng.

## Cài đặt

```bash
git clone <PRIVATE_REPOSITORY_URL>
cd <REPOSITORY_DIRECTORY>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Trên Windows, kích hoạt môi trường bằng `.venv\Scripts\activate`.

## Biến môi trường

Sao chép `.env.example` thành `.env` nếu cần ghi lại cấu hình cục bộ. Ứng dụng không tự đọc `.env`; hãy export biến trong shell hoặc dùng công cụ quản lý môi trường của hệ điều hành.

- `AB_HOST`: địa chỉ bind, mặc định `127.0.0.1`.
- `AB_PORT`: cổng, mặc định `8765`.
- `AB_DATA_DIR`: thư mục database và media, mặc định `./data`.
- `AB_OUTPUT_DIR`: thư mục tệp xuất, mặc định `./outputs`.

`.env`, database, video, file upload và output đều bị loại khỏi Git.

## Khởi tạo database

```bash
python scripts/init_db.py
```

Ứng dụng cũng tự tạo hai bảng `sessions` và `history` khi khởi động nếu database chưa có. `schema.sql` là schema có thể kiểm tra và dùng để dựng database mới.

Tạo dữ liệu tổng hợp an toàn để thử:

```bash
python demo_build.py
```

Lệnh này tạo video tổng hợp và phiên `SYNTHETIC_KNOWN_ANSWER` trong thư mục runtime bị Git bỏ qua. Không tạo hoặc tải video công khai.

## Chạy development server

```bash
python app.py
```

Mở http://127.0.0.1:8765. Trên macOS có thể bấm đúp `Start.command` sau khi tạo `.venv`.

Để chạy một bản kiểm tra song song trên cổng khác:

```bash
AB_PORT=8766 python app.py
```

## Kiểm thử

Với database thử riêng:

```bash
AB_DATA_DIR=/tmp/video-ab-test-data AB_OUTPUT_DIR=/tmp/video-ab-test-output python demo_build.py
AB_DATA_DIR=/tmp/video-ab-test-data AB_OUTPUT_DIR=/tmp/video-ab-test-output python tests.py -q
```

## Dữ liệu và backup

Không commit `data/`, `demo/`, `outputs/`, database SQLite hoặc video khảo sát. Sao lưu đồng thời:

- `data/survey.sqlite`;
- toàn bộ `data/media/`;
- cấu hình môi trường dùng khi chạy.

Database lưu media ID, còn `index.json` trong kho media được phân giải lại theo thư mục hiện tại. Vì vậy có thể di chuyển một backup đầy đủ gồm database và media sang đường dẫn khác.

## Upload và triển khai

Hiện ứng dụng nhận hai loại upload:

- video A/B, được lưu cục bộ trong `data/media/`;
- snapshot JSON, được nhập thành một phiên mới.

Chưa có upload PDF, Word, Excel hoặc hồ sơ tổng quát. Cơ chế local storage phù hợp chạy một người trên máy cá nhân. Khi triển khai nhiều instance hoặc trên hạ tầng có filesystem tạm thời, cần thiết kế object storage và database dùng chung trước; không chỉ đổi đường dẫn.

## Tài liệu phát triển

- `docs/USER_GUIDE_VI.md`: hướng dẫn sử dụng từng bước bằng tiếng Việt.
- `docs/HUONG_DAN_SU_DUNG_CO_HINH_MINH_HOA.docx`: hướng dẫn Word có ảnh chụp màn hình, dành cho người mới sử dụng máy tính và chưa có kinh nghiệm nghiên cứu.
- `PROJECT_MANIFEST.md`: kiến trúc, API, dữ liệu và các giới hạn.
- `AI_CONTEXT.md`: ngữ cảnh ngắn dành cho ChatGPT/Codex.
- `docs/METHOD_TRACEABILITY.md`: đối chiếu yêu cầu phương pháp.
- `docs/TEST_REPORT.md`: phạm vi kiểm thử chức năng khoa học.
