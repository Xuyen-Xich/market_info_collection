from typing import Dict, Any

from playwright.sync_api import Page

from base_scraper import BaseScraper


class TuoiTreScraper(BaseScraper):
    SOURCE_NAME = "TuoiTre"

    def parse_article(self, url: str, page: Page) -> Dict[str, Any]:
        soup = self.load_page(page, url)

        title = self.extract_text(soup, ["h1.title-detail", "h1.article-title", "h1"])
        date_text = self.extract_text(soup, ["div.date-time", "span.date-time", "time"])
        content_block = soup.select_one("div.article-content") or soup.select_one("article")

        return {
            "title": title or "Tiêu đề không xác định",
            "date": self.parse_date(date_text),
            "source": self.SOURCE_NAME,
            "url": url,
            "content": self.clean_html(content_block),
            "tags": ["dữ_liệu_cào", "tuổi trẻ", "kinh_tế_đời_sống"],
        }
