import re
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

        # Nếu URL không phải trang bài (.html/.htm) coi là trang chuyên mục / list page
        if not url.lower().endswith(".html") and not url.lower().endswith(".htm"):
            # Lấy tất cả anchor dẫn tới .html và lọc thành các liên kết bài báo thực sự
            anchors = soup.select('a[href$=".html"], a[href$=".htm"]')
            urls: List[str] = []
            seen: set = set()
            for a in anchors:
                href = a.get("href")
                if not href:
                    continue
                if href.startswith("#") or href.lower().startswith("javascript:"):
                    continue
                full_url = urljoin(url, href.split("#")[0].strip())
                parsed = urlparse(full_url)
                if parsed.netloc and "vnexpress.net" not in parsed.netloc:
                    continue
                # Chỉ chọn các URL có dạng bài báo của VnExpress: kết thúc bằng -<digits>.html
                if not re.search(r"-\d+\.html$", full_url):
                    continue
                full_url_norm = full_url
                if full_url_norm in seen:
                    continue
                seen.add(full_url_norm)
                urls.append(full_url_norm)

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
            "tags": self.extract_page_tags(
                soup,
                fallback=["dữ_liệu_cào", "vnexpress", "kinh_tế_đời_sống"],
            ),
        }
