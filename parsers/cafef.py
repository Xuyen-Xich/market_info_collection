import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

from loguru import logger
from bs4 import BeautifulSoup
from playwright.sync_api import Page

from base_scraper import BaseScraper


class CafeFScraper(BaseScraper):
    """Parser cho trang CafeF (cafef.vn).
    
    Trang CafeF cung cấp thông tin tài chính, chứng khoán, giá cà phê.
    URL có dạng: https://cafef.vn/[slug]-[id].chn
    """

    SOURCE_NAME = "CafeF"
    OUTPUT_SUBDIR = "cafef"

    def parse_article(self, url: str, page: Page) -> Dict[str, Any]:
        soup = self.load_page(page, url)

        # Kiểm tra xem có phải trang danh sách (list page) không
        # Ưu tiên kiểm tra: URL patterns trước, sau đó kiểm tra content
        
        # 1. Kiểm tra URL patterns
        has_list_pattern = any(pattern in url.lower() for pattern in [
            '/doc-nhanh',
            '/tag/',
            '/search',
            '/category/',
            '/danh-muc-',
        ])
        
        # 2. Kiểm tra xem có content block (article) không
        has_content_block = bool(
            soup.select_one("div.contentdetail") or 
            soup.select_one("div.left_cate.totalcontentdetail")
        )
        
        # Chỉ coi là list page nếu match URL pattern hoặc (không có content AND có nhiều links)
        anchors = soup.select('a[href$=".chn"]')
        is_list_page = has_list_pattern or (not has_content_block and len(anchors) > 20)
        
        if is_list_page:
            urls: List[str] = []
            seen: set = set()
            
            for a in anchors:
                href = a.get("href")
                if not href:
                    continue
                if href.startswith("#") or href.lower().startswith("javascript:"):
                    continue
                
                # Dọn URL
                cleaned = href.split("#")[0].strip()
                if not cleaned:
                    continue
                
                # Chuyển relative URL thành absolute
                full_url = urljoin(url, cleaned)
                parsed = urlparse(full_url)
                
                # Kiểm tra domain
                if parsed.netloc and "cafef.vn" not in parsed.netloc:
                    continue
                
                # Kiểm tra duplicate
                full_url_norm = full_url.lower()
                if full_url_norm in seen:
                    continue
                
                # Lọc ra các URL không phải bài viết
                if "/rss" in full_url_norm or "-rss" in full_url_norm:
                    logger.debug(f"Bỏ qua URL RSS không phải bài viết: {full_url}")
                    continue
                
                # Bỏ qua chính trang hiện tại
                if full_url_norm == url.lower():
                    continue
                
                seen.add(full_url_norm)
                urls.append(full_url)
            
            logger.info(f"Phát hiện {len(urls)} liên kết bài viết từ trang danh mục {url}")
            return {
                "list_urls": urls,
                "source": self.SOURCE_NAME,
            }

        # Xử lý trang bài viết đơn lẻ
        title = self.extract_text(soup, [
            "h1.title",
            "h1",
        ])

        # Tìm ngày đầy đủ từ meta tag hoặc time element
        date_text = None
        
        # Kiểm tra meta tag article:published_time trước (ISO format)
        meta_published = soup.select_one("meta[property='article:published_time']")
        if meta_published and meta_published.get('content'):
            date_text = meta_published['content']
        else:
            # Fallback: lấy từ span.time.timeliveheader
            date_text = self.extract_text(soup, [
                "span.time.timeliveheader",
                "span.time",
            ])

        # Tìm content block - thứ tự ưu tiên
        content_block = soup.select_one(
            "div.contentdetail, div.left_cate.totalcontentdetail"
        )

        content_markdown = self.clean_html(content_block)

        # Trích xuất tags từ page metadata
        tags = self.extract_page_tags(
            soup,
            fallback=["dữ_liệu_cào", "cafef", "kinh_tế_tài_chính"],
        )

        return {
            "title": title or "Tiêu đề không xác định",
            "date": self.parse_date(date_text),
            "source": self.SOURCE_NAME,
            "url": url,
            "content": content_markdown,
            "tags": tags,
        }
