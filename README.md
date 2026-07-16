# RetailNewsCrawler

Mục tiêu: thu thập bài viết báo trực tuyến và xuất mỗi bài thành một file Markdown (.md) tương thích với Obsidian, kèm YAML frontmatter.

**Tính năng chính**
- Thu thập bài báo từ nhiều nguồn (ví dụ: VnExpress, Reuters, CafeF).
- Hỗ trợ trang chuyên mục (list pages) để lấy danh sách bài trong chuyên mục.
- Lưu từng bài thành file Markdown riêng, định dạng chuẩn (YAML frontmatter + nội dung Markdown).
- Lịch sử crawl bằng SQLite để hỗ trợ incremental crawling, tránh trùng lặp.
- Lọc theo độ tuổi bài viết (`--max-age-days`) và tùy chọn `--force-recrawl` để ghi đè.

**Yêu cầu**
- Python 3.10+
- Thư viện trong `requirements.txt`

**Cài đặt nhanh**
1. Tạo virtualenv và cài phụ thuộc:

```bash
python -m venv .venv
.
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

2. (Tùy chọn) Cài Playwright nếu chưa có:

```bash
playwright install
```

**Chạy crawler**
- Chạy một URL đơn lẻ:

```bash
python main.py --url https://vnexpress.net/some-article.html --output-dir output
```

- Chạy từ file danh sách URL (`urls.txt`):

```bash
python main.py --urls-file urls.txt --output-dir output --max-age-days 7
```

- Tùy chọn quan trọng:
  - `--max-age-days N`: chỉ lưu bài có ngày đăng trong N ngày gần nhất.
  - `--force-recrawl`: bắt buộc tải lại và ghi đè file đã có.

**Đầu ra**
- Thư mục mặc định: `output/`.
- Mỗi bài được lưu một file Markdown: `YYYY-MM-DD-slugified-title.md`.
- File Markdown có YAML frontmatter (title, date, source, url, tags).
- Crawl history: `output/.crawler.db` (SQLite) lưu `url`, `title`, `date`, `saved_path`, `crawled_at`.

**Quy ước đặt tên / slug**
- Bỏ dấu (unicode normalization), map `đ` → `d`, chuyển chữ hoa → thường, thay khoảng trắng bằng `-`.
- File canonical được giữ; các bản duplicate có cùng slug nhưng khác tiền tố ngày sẽ bị loại.

**Cấu trúc dự án (tổng quan)**
- **Tập tin chính**:
  - [main.py](main.py#L1): điểm vào CLI.
  - [base_scraper.py](base_scraper.py#L1): lớp cơ sở xử lý trình duyệt, lưu file, DB lịch sử.
  - [requirements.txt](requirements.txt#L1): danh sách phụ thuộc.
- **Thư mục**:
  - `parsers/`: bộ parser theo site (ví dụ [parsers/vne.py](parsers/vne.py#L1)).
  - `scripts/`: helper scripts và runner (ví dụ [scripts/run.py](scripts/run.py#L1)).
  - `output/`: nơi lưu Markdown và file DB lịch sử.
  - `src/`, `tests/`: mã nguồn bổ sung và kiểm thử (nếu có).

**Các file quan trọng khác**
- [config.example.toml](config.example.toml#L1): ví dụ config.
- [CRAWLING_RULES.md](CRAWLING_RULES.md#L1): quy tắc thu thập và xử lý nội dung.

**Phát triển & đóng góp**
- Tuân thủ coding standard trong `CODING_STANDARD.md`.
- Thêm parser mới: tạo file trong `parsers/` kế thừa interface parser hiện có và trả về `title`, `date`, `content` hoặc `list_urls` cho trang chuyên mục.
- Chạy tests: (nếu có) `pytest`.

**Ví dụ nhanh: crawl chuyên mục VnExpress**

1. Tạo file `urls.txt` chứa:

```
https://vnexpress.net/kinh-doanh
```

2. Chạy:

```bash
python main.py --urls-file urls.txt --output-dir output --max-age-days 30
```

3. Kiểm tra kết quả trong `output/` và DB `output/.crawler.db`.

**Vấn đề thường gặp**
- Trùng file do khác tiền tố ngày: công cụ sẽ cố gắng canonicalize slug và xóa duplicate cùng slug.
- Vấn đề với Playwright/Chrome: nếu không tìm thấy Chrome, script dùng fallback hoặc yêu cầu `playwright install`.

**License & Liên hệ**
- Xem file `LICENSE` cho thông tin giấy phép.
- Thắc mắc / báo lỗi: mở issue trên repository.

----------
File này được tạo tự động bởi trợ lý; cần chỉnh ngôn ngữ hoặc thêm ví dụ cụ thể, tôi sẽ cập nhật.
