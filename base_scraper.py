import random
import re
import time
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse
import sqlite3
from datetime import timezone, timedelta

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from loguru import logger
from markdownify import markdownify as html_to_markdown
from playwright.sync_api import Browser, Error, Page, sync_playwright


@dataclass
class ScraperConfig:
    """Cấu hình chung cho toàn bộ bộ cào."""
    debugger_address: Optional[str] = "http://localhost:9222"
    proxy: Optional[str] = None
    output_dir: Path = Path("output")
    min_delay: float = 3.0
    max_delay: float = 7.0
    headless: bool = True
    timeout_seconds: int = 45000
    # If set, skip articles older than this many days (incremental crawling)
    max_age_days: Optional[int] = None
    # If True, ignore crawl history and re-download
    force_recrawl: bool = False


class BaseScraper(ABC):
    """Lớp cha dùng chung cho tất cả parser cụ thể.

    Nó kết nối tới Cloakbrowser qua Playwright CDP,
    tạo delay ngẫu nhiên giữa các request, và lưu output Markdown.
    """

    SOURCE_NAME = "Generic"
    OUTPUT_SUBDIR: Optional[str] = None

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self._db_conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def get_output_subdir(self) -> str:
        if self.OUTPUT_SUBDIR:
            return self.OUTPUT_SUBDIR
        return self.slugify(self.SOURCE_NAME)

    def get_output_dir(self) -> Path:
        output_dir = self.output_dir / self.get_output_subdir()
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def __enter__(self):
        self.setup_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_browser()

    def setup_browser(self) -> None:
        """Khởi tạo browser từ Cloakbrowser hoặc local nếu không kết nối được."""
        self.playwright = sync_playwright().start()
        if self.config.debugger_address:
            logger.info(f"Kết nối Cloakbrowser qua CDP: {self.config.debugger_address}")
            try:
                self.browser = self.playwright.chromium.connect_over_cdp(self.config.debugger_address)
                return
            except Error as exc:
                logger.warning(f"Kết nối CDP trực tiếp thất bại: {exc}")
                ws_url = self.config.debugger_address.replace("http://", "ws://").replace("https://", "wss://")
                logger.info(f"Thử lại với websocket: {ws_url}")
                try:
                    self.browser = self.playwright.chromium.connect_over_cdp(ws_url)
                    return
                except Error as exc2:
                    logger.warning(f"Kết nối websocket Cloakbrowser thất bại: {exc2}")
                    logger.info("Chuyển sang khởi chạy trình duyệt local để tiếp tục cào.")

        logger.info("Khởi chạy trình duyệt cục bộ")
        launch_args = {"headless": self.config.headless}
        if self.config.proxy:
            launch_args["proxy"] = {"server": self.config.proxy}

        local_executable = self.find_local_chrome()
        if local_executable:
            launch_args["executable_path"] = local_executable

        self.browser = self.playwright.chromium.launch(**launch_args)

    def close_browser(self) -> None:
        """Đóng browser và giải phóng tài nguyên."""
        if self.browser:
            try:
                self.browser.close()
            except Exception as exc:
                logger.warning(f"Không đóng browser được: {exc}")
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as exc:
                logger.warning(f"Không dừng Playwright được: {exc}")
        self._close_db()

    def find_local_chrome(self) -> Optional[str]:
        """Tìm đường dẫn Chromium/Chrome cục bộ để dùng fallback khi không có Playwright browser."""
        common_paths = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        ]
        for path in common_paths:
            if path.exists():
                logger.info(f"Tìm thấy browser cục bộ: {path}")
                return str(path)
        logger.warning("Không tìm thấy Chrome/Edge cục bộ trong các đường dẫn chuẩn.")
        return None

    def _init_db(self) -> None:
        try:
            db_path = self.output_dir / ".crawler.db"
            self._db_conn = sqlite3.connect(str(db_path))
            cur = self._db_conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS crawled (
                    url TEXT PRIMARY KEY,
                    title TEXT,
                    date TEXT,
                    saved_path TEXT,
                    crawled_at TEXT
                )
                """
            )
            self._db_conn.commit()
        except Exception:
            self._db_conn = None

    def _close_db(self) -> None:
        if self._db_conn:
            try:
                self._db_conn.close()
            except Exception:
                pass

    def sleep_between_requests(self) -> None:
        """Delay ngẫu nhiên giữa các request để giảm xác suất bị block."""
        delay = random.uniform(self.config.min_delay, self.config.max_delay)
        logger.info(f"Tạm dừng {delay:.2f}s trước khi thực hiện request tiếp theo")
        time.sleep(delay)

    def clean_text(self, text: str) -> str:
        return " ".join(text.split()) if text else ""

    def remove_diacritics(self, text: str) -> str:
        # Normalize and remove combining diacritics, then handle special Vietnamese letters
        if not text:
            return ""
        # Map special Vietnamese letter 'đ' to 'd' (and uppercase variant)
        text = text.replace("đ", "d").replace("Đ", "D")
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    def slugify(self, text: str) -> str:
        text = self.remove_diacritics(text).lower().strip()
        text = re.sub(r"[^a-z0-9\s-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        return text.strip("-") or "untitled"

    def save_markdown(
        self,
        title: str,
        date: datetime,
        url: str,
        source: str,
        content_markdown: str,
        tags: Optional[List[str]] = None,
        existing_path: Optional[Path] = None,
    ) -> Path:
        """Lưu bài viết dưới dạng file Markdown phù hợp Obsidian."""
        file_name = f"{date.strftime('%Y-%m-%d')}-{self.slugify(title)}.md"
        base_dir = self.get_output_dir()
        file_path = Path(existing_path) if existing_path else (base_dir / file_name)
        tags = tags or ["du_lieu_cao", "tin_tuc"]

        frontmatter = [
            "---",
            f"title: \"{title}\"",
            f"date: {date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"source: \"{source}\"",
            f"url: \"{url}\"",
            "tags:",
            *(f"  - {tag}" for tag in tags),
            "---",
            "",
            f"# {title}",
            "",
        ]

        text = "\n".join(frontmatter) + content_markdown.strip() + "\n"
        file_path.write_text(text, encoding="utf-8")
        logger.success(f"Lưu xong: {file_path}")
        return file_path

    def parse_date(self, date_value: Any) -> datetime:
        """Chuẩn hóa ngày tháng sang datetime object."""
        if isinstance(date_value, datetime):
            return date_value
        if not date_value:
            return datetime.now()
        try:
            return date_parser.parse(str(date_value), fuzzy=True)
        except Exception:
            logger.warning(f"Không parse được date: {date_value}, dùng giờ hiện tại")
            return datetime.now()

    def _has_been_crawled(self, url: str) -> bool:
        if not self._db_conn:
            return False
        try:
            cur = self._db_conn.cursor()
            canon = self._canonicalize_url(url)
            cur.execute("SELECT 1 FROM crawled WHERE url = ? OR url = ?", (canon, url))
            return cur.fetchone() is not None
        except Exception:
            return False

    def _mark_crawled(self, url: str, title: str, date: datetime, saved_path: str) -> None:
        if not self._db_conn:
            return
        try:
            cur = self._db_conn.cursor()
            cur.execute(
                "REPLACE INTO crawled (url, title, date, saved_path, crawled_at) VALUES (?, ?, ?, ?, ?)",
                (self._canonicalize_url(url), title, date.isoformat(), saved_path, datetime.now(timezone.utc).isoformat()),
            )
            self._db_conn.commit()
        except Exception:
            pass

    def _get_saved_path(self, url: str) -> Optional[str]:
        if not self._db_conn:
            return None
        try:
            cur = self._db_conn.cursor()
            canon = self._canonicalize_url(url)
            cur.execute("SELECT saved_path FROM crawled WHERE url = ? OR url = ?", (canon, url))
            row = cur.fetchone()
            return row[0] if row else None
        except Exception:
            return None

    def _canonicalize_url(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            cleaned = parsed._replace(query="", fragment="")
            out = urlunparse(cleaned)
            if out.endswith("/"):
                out = out[:-1]
            return out
        except Exception:
            return url

    def clean_html(self, element: Any) -> str:
        """Dọn HTML, loại bỏ quảng cáo và thành phần không cần thiết."""
        if element is None:
            return ""

        soup = element if isinstance(element, BeautifulSoup) else BeautifulSoup(str(element), "lxml")
        for selector in [
            "script",
            "style",
            "noscript",
            "iframe",
            "header",
            "footer",
            "nav",
            "aside",
            "form",
            "figure",
            "img",
            "svg",
            "button",
            "input",
            "figure",
            "blockquote.ad",
        ]:
            for tag in soup.select(selector):
                tag.decompose()

        for class_key in ["ads", "advert", "banner", "subscribe", "related", "comment", "sidebar"]:
            for tag in soup.select(f"*[class*=' {class_key}'], *[class*='{class_key}']"):
                tag.decompose()

        for article_head in soup.select(".share, .tag, .related-post, .pagination, .breadcrumb, .toolbar"):
            article_head.decompose()

        return html_to_markdown(str(soup), heading_style="ATX", bullets="-", wrap_links=False)

    def extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = self.clean_text(element.get_text(" ", strip=True))
                if text:
                    return text
        return None

    def normalize_tag(self, tag: str) -> str:
        if not tag:
            return ""
        normalized = self.slugify(self.clean_text(tag))
        return normalized.replace("-", "_")

    def extract_meta_keywords(self, soup: BeautifulSoup) -> List[str]:
        meta = soup.select_one("meta[name='keywords']")
        if not meta or not meta.get("content"):
            return []
        keywords = [item.strip() for item in meta["content"].split(",") if item.strip()]
        tags: List[str] = []
        seen: set = set()
        for keyword in keywords:
            normalized = self.normalize_tag(keyword)
            if normalized and normalized not in seen:
                seen.add(normalized)
                tags.append(normalized)
        return tags

    def extract_meta_section(self, soup: BeautifulSoup) -> List[str]:
        selectors = ["meta[property='article:section']", "meta[name='article:section']"]
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get("content"):
                normalized = self.normalize_tag(element.get("content"))
                if normalized:
                    return [normalized]
        return []

    def extract_breadcrumb_tags(self, soup: BeautifulSoup) -> List[str]:
        selectors = [
            "nav.breadcrumb a",
            "div.breadcrumb a",
            "div.bread-crumb a",
            "ul.breadcrumb a",
            "li.breadcrumb a",
            "nav.breadcrumb li a",
        ]
        tags: List[str] = []
        seen: set = set()
        stop_words = {"home", "trang chủ", "vietnamnet news", "vnexpress", "vnexpress.net"}
        for selector in selectors:
            for anchor in soup.select(selector):
                text = self.clean_text(anchor.get_text(" ", strip=True))
                if not text:
                    continue
                if text.lower() in stop_words:
                    continue
                normalized = self.normalize_tag(text)
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    tags.append(normalized)
        return tags

    def extract_page_tags(self, soup: BeautifulSoup, fallback: Optional[List[str]] = None, max_tags: int = 12) -> List[str]:
        tags: List[str] = []
        seen: set = set()
        for candidate in self.extract_meta_section(soup) + self.extract_breadcrumb_tags(soup) + self.extract_meta_keywords(soup):
            if candidate and candidate not in seen:
                seen.add(candidate)
                tags.append(candidate)
                if len(tags) >= max_tags:
                    break
        if not tags and fallback:
            for tag in fallback:
                normalized = self.normalize_tag(tag)
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    tags.append(normalized)
        return tags

    def load_page(self, page: Page, url: str) -> BeautifulSoup:
        """Mở URL và trả về BeautifulSoup của nội dung đã render."""
        logger.info(f"Mở trang: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_seconds)
        self.sleep_between_requests()
        return BeautifulSoup(page.content(), "lxml")

    def run_article_page(self, url: str, context) -> Optional[Path]:
        """Chạy parser cho một bài viết đơn lẻ trong cùng context browser."""
        page = context.new_page()
        try:
            result = self.parse_article(url, page)
            if not isinstance(result, dict):
                raise ValueError("parse_article must return a dict for article pages")
            if "list_urls" in result:
                raise ValueError("Nested list pages are not supported in run_article_page")

            title = result.get("title", "Untitled")
            date = self.parse_date(result.get("date"))

            # Skip based on max_age_days
            max_age = self.config.max_age_days
            if max_age is not None:
                try:
                    cutoff = datetime.now(timezone.utc) - timedelta(days=int(max_age))
                    if date.tzinfo is None:
                        date_cmp = date.replace(tzinfo=timezone.utc)
                    else:
                        date_cmp = date.astimezone(timezone.utc)
                    if date_cmp < cutoff:
                        logger.info(f"Bỏ qua bài {url} vì cũ hơn {max_age} ngày")
                        return None
                except Exception:
                    pass

            content = result.get("content", "")
            tags = result.get("tags", ["du_lieu_cao", "tin_tuc"])

            # Check existing saved path and normalize filename before skipping
            existing = self._get_saved_path(url)
            expected_name = f"{date.strftime('%Y-%m-%d')}-{self.slugify(title)}.md"
            expected_path = self.get_output_dir() / expected_name

            if existing:
                existing_path = Path(existing)
                if existing_path.exists() and existing_path.resolve() != expected_path.resolve():
                    try:
                        if expected_path.exists():
                            existing_path.unlink()
                        else:
                            existing_path.replace(expected_path)
                        self._mark_crawled(url, title, date, str(expected_path))
                        existing = str(expected_path)
                        existing_path = expected_path
                    except Exception:
                        pass

            # Remove other files with same slug (different date prefixes) to avoid duplicates
            try:
                slug = self.slugify(title)
                matches = list(self.get_output_dir().glob(f"*-{slug}.md"))
                if len(matches) > 1:
                    # decide canonical to keep: expected_path if exists, else first existing
                    keep = expected_path if expected_path.exists() else (Path(matches[0]) if matches else None)
                    for m in matches:
                        if keep and m.resolve() == keep.resolve():
                            continue
                        try:
                            m.unlink()
                        except Exception:
                            pass
            except Exception:
                pass

            # Skip if already crawled (unless force_recrawl)
            if existing and not self.config.force_recrawl:
                logger.info(f"Đã có file lưu trước đó tại {existing}, bỏ qua lưu mới: {url}")
                return Path(existing)

            if existing and self.config.force_recrawl:
                saved = self.save_markdown(title, date, url, result.get("source", self.SOURCE_NAME), content, tags, existing_path=Path(existing))
            else:
                saved = self.save_markdown(title, date, url, result.get("source", self.SOURCE_NAME), content, tags)
            try:
                self._mark_crawled(url, title, date, str(saved))
            except Exception:
                pass
            return saved
        except Exception as exc:
            logger.error(f"Lỗi khi cào bài viết {url}: {exc}")
            return None
        finally:
            page.close()

    @abstractmethod
    def parse_article(self, url: str, page: Page) -> Dict[str, Any]:
        """Parser cụ thể mỗi site phải implement."""
        raise NotImplementedError("Phải cài đặt parse_article ở scraper con")

    def run(self, url: str, depth: int = 0, max_depth: int = 2) -> Optional[Path]:
        """Chạy parser với một URL và lưu file Markdown.
        
        Hỗ trợ nested list pages với giới hạn độ sâu.
        """
        if not self.browser:
            raise RuntimeError("Browser chưa được khởi tạo. Hãy sử dụng context manager hoặc gọi setup_browser().")

        # Ngăn chặn vòng lặp vô hạn với nested list pages
        if depth > max_depth:
            logger.warning(f"Đạt giới hạn độ sâu nested list pages ({max_depth}), bỏ qua: {url}")
            return None

        context = self.browser.new_context()
        page = context.new_page()
        try:
            result = self.parse_article(url, page)
            if isinstance(result, dict) and "list_urls" in result:
                saved_paths = []
                for item_url in result["list_urls"]:
                    # Xử lý nested list pages bằng cách gọi run_article_page_or_list
                    saved = self._process_url(item_url, context, depth + 1, max_depth)
                    if saved:
                        saved_paths.append(saved)
                if saved_paths:
                    logger.success(f"Lưu xong {len(saved_paths)} bài viết từ trang danh mục {url}")
                    return saved_paths[0]
                return None

            # For single-article pages reuse run_article_page to apply DB checks
            page.close()
            return self.run_article_page(url, context)
        except Exception as exc:
            logger.error(f"Lỗi khi cào {url}: {exc}")
            return None
        finally:
            page.close()
            context.close()

    def _process_url(self, url: str, context, depth: int = 0, max_depth: int = 2) -> Optional[Path]:
        """Xử lý một URL - có thể là article hoặc list page."""
        page = context.new_page()
        try:
            result = self.parse_article(url, page)
            if isinstance(result, dict) and "list_urls" in result:
                # Đây là list page - xử lý đệ quy
                if depth > max_depth:
                    logger.warning(f"Đạt giới hạn độ sâu ({max_depth}), bỏ qua nested list: {url}")
                    return None
                    
                saved_paths = []
                for item_url in result["list_urls"]:
                    saved = self._process_url(item_url, context, depth + 1, max_depth)
                    if saved:
                        saved_paths.append(saved)
                
                if saved_paths:
                    logger.info(f"Lưu xong {len(saved_paths)} bài từ nested list: {url}")
                    return saved_paths[0]
                return None
            else:
                # Đây là article page - xử lý bình thường
                page.close()
                return self.run_article_page(url, context)
        except Exception as exc:
            logger.error(f"Lỗi khi xử lý URL {url}: {exc}")
            return None
        finally:
            page.close()

    @classmethod
    def supports_url(cls, url: str) -> bool:
        parsed = urlparse(url)
        return cls.SOURCE_NAME.lower() in parsed.netloc.lower()
