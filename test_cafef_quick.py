#!/usr/bin/env python3
"""Quick test of CafeF parser."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from bs4 import BeautifulSoup
from parsers.cafef import CafeFScraper
from base_scraper import ScraperConfig

def test_parse_single_article():
    """Test parsing a single article without browser."""
    from playwright.sync_api import sync_playwright
    
    url = "https://cafef.vn/tu-ngay-mai-17-7-dich-vu-hang-trieu-nguoi-dang-dung-thay-doi-cach-tinh-gia-ve-188260716214944455.chn"
    
    config = ScraperConfig(
        headless=True,
        output_dir=Path("output"),
    )
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        scraper = CafeFScraper(config)
        
        # Load page and test parse_article
        result = scraper.parse_article(url, page)
        
        print(f"\n{'='*60}")
        print("PARSE RESULT")
        print('='*60)
        print(f"Title: {result.get('title', 'N/A')[:60]}...")
        print(f"Date: {result.get('date', 'N/A')}")
        print(f"Source: {result.get('source', 'N/A')}")
        print(f"URL: {result.get('url', 'N/A')}")
        content = result.get('content', '')
        print(f"Content length: {len(content)} chars")
        print(f"Content preview: {content[:100]}...")
        print(f"Tags: {result.get('tags', [])}")
        
        page.close()
        context.close()
        browser.close()
        
        return result

if __name__ == "__main__":
    test_parse_single_article()
    print("\n✓ Test completed successfully!")
