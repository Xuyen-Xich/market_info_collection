#!/usr/bin/env python3
"""Test CafeF list page parsing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parsers.cafef import CafeFScraper
from base_scraper import ScraperConfig
from playwright.sync_api import sync_playwright

def test_list_page():
    """Test parsing a list page."""
    url = "https://cafef.vn/doc-nhanh.chn"
    
    config = ScraperConfig(
        headless=True,
        output_dir=Path("output"),
    )
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        scraper = CafeFScraper(config)
        
        # Parse list page
        result = scraper.parse_article(url, page)
        
        print(f"\n{'='*60}")
        print("LIST PAGE PARSE RESULT")
        print('='*60)
        
        if 'list_urls' in result:
            urls = result['list_urls']
            print(f"Total URLs found: {len(urls)}")
            print(f"Source: {result.get('source', 'N/A')}")
            print(f"\nFirst 5 URLs:")
            for i, url in enumerate(urls[:5], 1):
                print(f"  {i}. {url}")
        else:
            print("No list_urls found in result")
            print(f"Result keys: {result.keys()}")
        
        page.close()
        context.close()
        browser.close()

if __name__ == "__main__":
    test_list_page()
    print("\n[OK] List page test completed!")
