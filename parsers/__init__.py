"""Gói parsers cho từng website."""
from .cafef import CafeFScraper
from .reuters import ReutersScraper
from .vne import VnExpressScraper
from .tuoitre import TuoiTreScraper
from .thanhnien import ThanhNienScraper
from .vietnamnet import VietnamNetScraper
from .sggp import SGGPscraper
from .nhipcaudautu import NhipCauDauTuScraper
from .retailnewsasia import RetailNewsAsiaScraper
from .vietnamlogisticsreview import VietnamLogisticsReviewScraper
from .vla import VLAScraper
from .worldpanelvietnam import WorldpanelVietnamScraper
from .agromonitor import AgromonitorScraper
from .mard import MARDscraper
from .monre import MONREscraper
from .moit import MoITScraper
from .gso import GSOScraper
from .nchmf import NCHMFScraper
from .nikkei import NikkeiScraper

__all__ = [
    "CafeFScraper",
    "ReutersScraper",
    "VnExpressScraper",
    "TuoiTreScraper",
    "ThanhNienScraper",
    "VietnamNetScraper",
    "SGGPscraper",
    "NhipCauDauTuScraper",
    "RetailNewsAsiaScraper",
    "VietnamLogisticsReviewScraper",
    "VLAScraper",
    "WorldpanelVietnamScraper",
    "AgromonitorScraper",
    "MARDscraper",
    "MONREscraper",
    "MoITScraper",
    "GSOScraper",
    "NCHMFScraper",
    "NikkeiScraper",
]
