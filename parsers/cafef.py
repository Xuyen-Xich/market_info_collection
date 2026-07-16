from datetime import datetime
from typing import Dict, Any

from bs4 import BeautifulSoup
from playwright.sync_api import Page

from base_scraper import BaseScraper


class CafeFScraper(BaseScraper):
    """Parser cho trang CafeF."""

    SOURCE_NAME = "CafeF"

    def parse_article(self, url: str, page: Page) -> Dict[str, Any]:
        soup = self.load_page(page, url)

        title = self.extract_text(soup, [
            "h1.title",
            "h1.entry-title",
            "h1",
        ])

        date_text = self.extract_text(soup, [
            "div.time",
            "span.time",
            "p.date",
            "div.article-meta",
        ])

        content_block = soup.select_one(
            "div.detail-content, div.fck_detail, div.article-content, div#ArticleContent"
        )
        if not content_block:
            content_block = soup.select_one("article")

        content_markdown = self.clean_html(content_block)

        return {
            "title": title or "Tiêu đề không xác định",
            "date": self.parse_date(date_text),
            "source": self.SOURCE_NAME,
            "url": url,
            "content": content_markdown,
            "tags": ["dữ_liệu_cào", "cafe_f", "kinh_tế_đời_sống"],
        }
