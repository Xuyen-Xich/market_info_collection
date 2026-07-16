import re
from typing import Dict, Any
from urllib.parse import urljoin, urlparse

from loguru import logger
from playwright.sync_api import Page

from base_scraper import BaseScraper


class VietnamNetScraper(BaseScraper):
    SOURCE_NAME = "VietnamNet"
    OUTPUT_SUBDIR = "vietnamnet"

    def parse_article(self, url: str, page: Page) -> Dict[str, Any]:
        soup = self.load_page(page, url)

        if "/kinh-doanh" in url and not url.endswith(".htm") and not url.endswith(".html"):
            anchors = soup.select('a[href$=".html"], a[href$=".htm"]')
            urls = []
            seen = set()
            for a in anchors:
                href = a.get("href")
                if not href:
                    continue
                if href.startswith("#") or href.lower().startswith("javascript:"):
                    continue
                cleaned = href.split("#")[0].strip()
                if not cleaned:
                    continue
                full_url = urljoin(url, cleaned)
                parsed = urlparse(full_url)
                if parsed.netloc and "vietnamnet.vn" not in parsed.netloc:
                    continue
                full_url_lower = full_url.lower()
                if full_url_lower in seen:
                    continue
                if "/tag" in full_url_lower or "-tag" in full_url_lower or "/rss" in full_url_lower or "-rss" in full_url_lower:
                    logger.debug(f"Bỏ qua URL tag/rss không phải bài viết: {full_url}")
                    continue
                if re.search(r'-page\d+\.html$', full_url_lower):
                    logger.debug(f"Bỏ qua URL phân trang không phải bài viết: {full_url}")
                    continue
                if not re.search(r'-(?:sk[0-9a-z]+|\d+)\.html$', full_url_lower):
                    logger.debug(f"Bỏ qua URL không phải bài viết: {full_url}")
                    continue
                seen.add(full_url_lower)
                urls.append(full_url)

            logger.info(f"Phát hiện {len(urls)} liên kết bài viết từ trang chuyên mục {url}")
            return {
                "list_urls": urls,
                "source": self.SOURCE_NAME,
            }

        title = self.extract_text(soup, ["h1.content-detail-title", "h1.title", "div.article-title", "h1"])
        date_text = self.extract_text(soup, ["p.time", "span.time", "time"])
        content_block = (
            soup.select_one("div.content-detail")
            or soup.select_one("div.content-detail.content-detail-type-1")
            or soup.select_one("div.maincontent")
            or soup.select_one("div.main-content")
            or soup.select_one("div#maincontent")
            or soup.select_one("article")
            or soup.select_one("div.container__left.not-pl")
            or soup.select_one("div.article-body")
            or soup.select_one("div.detail-content")
        )

        if content_block is None:
            logger.warning(f"Không tìm thấy content_block cho VietnamNet: {url}")

        return {
            "title": title or "Tiêu đề không xác định",
            "date": self.parse_date(date_text),
            "source": self.SOURCE_NAME,
            "url": url,
            "content": self.clean_html(content_block),
            "tags": ["dữ_liệu_cào", "vietnamnet", "kinh_tế_đời_sống"],
        }
