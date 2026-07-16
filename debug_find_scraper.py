#!/usr/bin/env python3
"""Debug find_scraper function."""

from main import find_scraper, PARSER_CLASSES
from loguru import logger

test_urls = [
    "https://vnexpress.net/khoa-hoc-cong-nghe",
    "https://cafef.vn/tu-ngay-mai-17-7-dich-vu-hang-trieu-nguoi-dang-dung-thay-doi-cach-tinh-gia-ve-188260716214944455.chn",
    "https://cafef.vn/doc-nhanh.chn",
]

print(f"Total parsers: {len(PARSER_CLASSES)}")
for cls in PARSER_CLASSES:
    print(f"  - {cls.__name__} (source: {cls.SOURCE_NAME})")

print("\n" + "="*60)
print("Testing find_scraper:")
print("="*60)

for url in test_urls:
    scraper_cls = find_scraper(url)
    if scraper_cls:
        print(f"✓ {url}")
        print(f"  -> {scraper_cls.__name__}")
    else:
        print(f"✗ {url}")
        print(f"  -> NO PARSER FOUND")
