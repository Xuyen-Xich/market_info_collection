#!/usr/bin/env python3
"""Quick test with a few URLs."""

from pathlib import Path
from base_scraper import ScraperConfig
from main import find_scraper
from loguru import logger

TEST_URLS = [
    "https://vnexpress.net/khoa-hoc-cong-nghe",
    "https://cafef.vn/tu-ngay-mai-17-7-dich-vu-hang-trieu-nguoi-dang-dung-thay-doi-cach-tinh-gia-ve-188260716214944455.chn",
]

def main():
    config = ScraperConfig(
        output_dir=Path("output"),
        headless=True,
        min_delay=2,
        max_delay=3,
    )
    
    logger.info(f"Test {len(TEST_URLS)} URLs")
    success_count = 0
    failed_count = 0
    
    for idx, url in enumerate(TEST_URLS, 1):
        logger.info(f"\n[{idx}/{len(TEST_URLS)}] Processing: {url}")
        
        scraper_cls = find_scraper(url)
        if not scraper_cls:
            logger.warning(f"No parser found for: {url}")
            failed_count += 1
            continue
        
        logger.info(f"Using parser: {scraper_cls.__name__}")
        try:
            with scraper_cls(config) as scraper:
                result = scraper.run(url)
                if result:
                    success_count += 1
                    logger.success(f"Success: {url}")
                else:
                    failed_count += 1
                    logger.warning(f"No result: {url}")
        except Exception as e:
            failed_count += 1
            logger.error(f"Error: {url}")
            logger.exception(e)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Summary:")
    logger.info(f"  Success: {success_count}/{len(TEST_URLS)}")
    logger.info(f"  Failed: {failed_count}/{len(TEST_URLS)}")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    main()
