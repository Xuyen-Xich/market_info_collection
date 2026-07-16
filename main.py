import argparse
from pathlib import Path
from typing import Dict, List, Optional

from base_scraper import BaseScraper, ScraperConfig
from parsers.cafef import CafeFScraper
from parsers.reuters import ReutersScraper
from parsers.vne import VnExpressScraper
from parsers.tuoitre import TuoiTreScraper
from parsers.thanhnien import ThanhNienScraper
from parsers.vietnamnet import VietnamNetScraper
from parsers.sggp import SGGPscraper
from parsers.nhipcaudautu import NhipCauDauTuScraper
from parsers.retailnewsasia import RetailNewsAsiaScraper
from parsers.vietnamlogisticsreview import VietnamLogisticsReviewScraper
from parsers.vla import VLAScraper
from parsers.worldpanelvietnam import WorldpanelVietnamScraper
from parsers.agromonitor import AgromonitorScraper
from parsers.mard import MARDscraper
from parsers.monre import MONREscraper
from parsers.moit import MoITScraper
from parsers.gso import GSOScraper
from parsers.nchmf import NCHMFScraper
from parsers.nikkei import NikkeiScraper


PARSER_CLASSES = [
    CafeFScraper,
    ReutersScraper,
    VnExpressScraper,
    TuoiTreScraper,
    ThanhNienScraper,
    VietnamNetScraper,
    SGGPscraper,
    NhipCauDauTuScraper,
    RetailNewsAsiaScraper,
    VietnamLogisticsReviewScraper,
    VLAScraper,
    WorldpanelVietnamScraper,
    AgromonitorScraper,
    MARDscraper,
    MONREscraper,
    MoITScraper,
    GSOScraper,
    NCHMFScraper,
    NikkeiScraper,
]

DEFAULT_URLS = [
    # Thêm URL bài viết thực tế vào đây.
    # Ví dụ:
    # "https://cafef.vn/example-article.chn",
    # "https://www.reuters.com/world/example-article/",
]


def find_scraper(url: str) -> Optional[BaseScraper]:
    for parser_cls in PARSER_CLASSES:
        if parser_cls.supports_url(url):
            return parser_cls
    return None


def load_urls_from_file(path: Path) -> List[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cloakbrowser News Crawler - obsdian markdown output")
    parser.add_argument("--urls-file", type=Path, help="Đường dẫn tới file chứa danh sách URL cần cào")
    parser.add_argument("--debugger-address", type=str, default="http://localhost:9222", help="Địa chỉ debugger của Cloakbrowser")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Thư mục lưu file Markdown")
    parser.add_argument("--min-delay", type=float, default=3.0, help="Delay tối thiểu giữa các request")
    parser.add_argument("--max-delay", type=float, default=7.0, help="Delay tối đa giữa các request")
    parser.add_argument("--headless", action="store_true", help="Chạy browser local ở chế độ headless khi không dùng debugger")
    parser.add_argument("--max-age-days", type=int, default=None, help="Chỉ cào các bài trong X ngày gần nhất")
    parser.add_argument("--force-recrawl", action="store_true", help="Bỏ qua lịch sử và cào lại mọi bài")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    urls = DEFAULT_URLS.copy()
    if args.urls_file and args.urls_file.exists():
        urls = load_urls_from_file(args.urls_file)

    if not urls:
        raise ValueError("Không có URL nào để cào. Thêm URL vào DEFAULT_URLS hoặc dùng --urls-file.")

    config = ScraperConfig(
        debugger_address=args.debugger_address,
        output_dir=args.output_dir,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        headless=args.headless,
        max_age_days=args.max_age_days,
        force_recrawl=args.force_recrawl,
    )

    for url in urls:
        scraper_cls = find_scraper(url)
        if not scraper_cls:
            print(f"Chưa có parser cho URL: {url}")
            continue

        print(f"[INFO] Sử dụng parser {scraper_cls.__name__} cho {url}")
        with scraper_cls(config) as scraper:
            scraper.run(url)


if __name__ == "__main__":
    main()
