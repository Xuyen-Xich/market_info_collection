#!/usr/bin/env python3
"""Test script for CafeF parser."""

from pathlib import Path
from base_scraper import ScraperConfig
from parsers.cafef import CafeFScraper

# Test URLs
TEST_URLS = [
    "https://cafef.vn/tu-ngay-mai-17-7-dich-vu-hang-trieu-nguoi-dang-dung-thay-doi-cach-tinh-gia-ve-188260716214944455.chn",
    "https://cafef.vn/jordan-danh-chan-hang-loat-ten-lua-iran-188260716211157095.chn",
    "https://cafef.vn/du-lieu/danh-muc-dau-tu.chn",  # Category page
]

def test_cafef():
    config = ScraperConfig(
        debugger_address=None,  # Use local browser
        headless=True,
        output_dir=Path("output"),
    )
    
    with CafeFScraper(config) as scraper:
        for url in TEST_URLS:
            print(f"\n{'='*60}")
            print(f"Testing: {url}")
            print('='*60)
            try:
                result = scraper.run(url)
                if result:
                    print(f"✓ Successfully saved: {result}")
                else:
                    print("✗ Failed to save")
            except Exception as e:
                print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_cafef()
