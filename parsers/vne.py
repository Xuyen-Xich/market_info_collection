from typing import Dict, Any, List
from urllib.parse import urljoin, urlparse

from loguru import logger
from playwright.sync_api import Page

from base_scraper import BaseScraper


class VnExpressScraper(BaseScraper):
    SOURCE_NAME = "VnExpress"
    OUTPUT_SUBDIR = "vne"

    def parse_article(self, url: str, page: Page) -> Dict[str, Any]:
        soup = self.load_page(page, url)

        if "/kinh-doanh" in url and not url.endswith(".html"):
            # Trang chuyên mục: trích xuất các bài báo bên trong
            anchors = soup.select('a[data-medium][href$=".html"]')
            urls: List[str] = []
            seen: set = set()
            for a in anchors:
                href = a.get("href")
                if not href:
                    continue
                if href.startswith("#") or href.lower().startswith("javascript:"):
                    continue
                full_url = urljoin(url, href.split("#")[0])
                parsed = urlparse(full_url)
                if parsed.netloc and "vnexpress.net" not in parsed.netloc:
                    continue
                if full_url in seen:
                    continue
                seen.add(full_url)
                urls.append(full_url)

            logger.info(f"Phát hiện {len(urls)} liên kết bài viết từ trang chuyên mục {url}")
            return {
                "list_urls": urls,
                "source": self.SOURCE_NAME,
            }

        title = self.extract_text(soup, ["h1.title-detail", "h1", "header h1"])
        date_text = self.extract_text(soup, ["span.date", "p.date-time", "div.datetime"])
        content_block = soup.select_one("article.fck_detail") or soup.select_one("div.container-detail")

        return {
            "title": title or "Tiêu đề không xác định",
            "date": self.parse_date(date_text),
            "source": self.SOURCE_NAME,
            "url": url,
            "content": self.clean_html(content_block),
            "tags": ["dữ_liệu_cào", "vnexpress", "kinh_tế_đời_sống"],
        }
