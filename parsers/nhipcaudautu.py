from typing import Dict, Any

from playwright.sync_api import Page

from base_scraper import BaseScraper


class NhipCauDauTuScraper(BaseScraper):
    SOURCE_NAME = "Nhip Cau Dau Tu"

    def parse_article(self, url: str, page: Page) -> Dict[str, Any]:
        soup = self.load_page(page, url)

        title = self.extract_text(soup, ["h1.title", "div.title-detail", "h1"])
        date_text = self.extract_text(soup, ["div.time", "span.time", "time"])
        content_block = soup.select_one("div.article-content") or soup.select_one("article")

        return {
            "title": title or "Tiêu đề không xác định",
            "date": self.parse_date(date_text),
            "source": self.SOURCE_NAME,
            "url": url,
            "content": self.clean_html(content_block),
            "tags": ["dữ_liệu_cào", "nhịp cầu đầu tư", "kinh_tế_đời_sống"],
        }
