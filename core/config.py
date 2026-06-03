import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CORE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = CORE_ROOT.parent

COMICVINE_API_KEY = (os.getenv("COMICVINE_API_KEY") or "").strip()

MAX_CONCURRENT_REQUESTS = 2 
REQUEST_TIMEOUT = 30
RETRY_TIMES = 3
REQUEST_DELAY = 0.5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

INPUT_FILE = PROJECT_ROOT / "销量.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "comic_sales_complete.xlsx"

DEFAULT_DATA_FILE = INPUT_FILE
ENRICHED_DATA_FILE = OUTPUT_FILE

LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

CACHE_DIR = PROJECT_ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_DB = CACHE_DIR / "comicvine_cache.db"
