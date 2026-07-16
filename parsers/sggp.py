from typing import Dict, Any

from playwright.sync_api import Page

from base_scraper import BaseScraper


class SGGPscraper(BaseScraper):
    SOURCE_NAME = "SGGP"

    def parse_article(self, url: str, page: Page) -> Dict[str, Any]:
        soup = self.load_page(page, url)

        title = self.extract_text(soup, ["h1.entry-title", "h1.title", "h1"])
        date_text = self.extract_text(soup, ["div.meta-info", "span.date", "time"])
        content_block = soup.select_one("div.content-detail") or soup.select_one("article")

        return {
            "title": title or "Tiêu đề không xác định",
            "date": self.parse_date(date_text),
            "source": self.SOURCE_NAME,
            "url": url,
            "content": self.clean_html(content_block),
            "tags": ["dữ_liệu_cào", "sggp", "kinh_tế_đời_sống"],
        }
