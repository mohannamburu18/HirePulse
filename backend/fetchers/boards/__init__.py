from .scrapling_boards import fetch_scrapling_jobs
from .crawl4ai_boards import fetch_crawl4ai_jobs
from .scrapegraph_boards import fetch_scrapegraph_jobs
from .merger import run_multi_scraper_boards

__all__ = [
    "fetch_scrapling_jobs",
    "fetch_crawl4ai_jobs",
    "fetch_scrapegraph_jobs",
    "run_multi_scraper_boards"
]

