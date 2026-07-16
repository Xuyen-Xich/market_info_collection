from typing import Dict, Any

from bs4 import BeautifulSoup
from playwright.sync_api import Page

from base_scraper import BaseScraper


class ReutersScraper(BaseScraper):
    """Parser cho trang Reuters."""

    SOURCE_NAME = "Reuters"

    def parse_article(self, url: str, page: Page) -> Dict[str, Any]:
        soup = self.load_page(page, url)

        title = self.extract_text(soup, [
            "h1",
            "div.ArticleHeader_headline",
            "div.headline",
        ])

        date_text = None
        time_tag = soup.select_one("time")
        if time_tag:
            date_text = time_tag.get("datetime") or time_tag.get_text(strip=True)

        content_block = soup.select_one(
            "div[data-testid='article-body-blocks'], article, div.StandardArticleBody_body"
        )
        if not content_block:
            content_block = soup.select_one("div.ArticleBodyWrapper")

        content_markdown = self.clean_html(content_block)

        return {
            "title": title or "Tiêu đề không xác định",
            "date": self.parse_date(date_text),
            "source": self.SOURCE_NAME,
            "url": url,
            "content": content_markdown,
            "tags": ["dữ_liệu_cào", "tin_quốc_tế", "reuters"],
        }
