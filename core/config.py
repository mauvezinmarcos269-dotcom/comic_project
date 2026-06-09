import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CORE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = CORE_ROOT.parent

# =====================
# API 配置
# =====================

COMICVINE_API_KEY = os.getenv("COMICVINE_API_KEY", "")

MAX_CONCURRENT_REQUESTS = 6
REQUEST_TIMEOUT = 30
RETRY_TIMES = 3
REQUEST_DELAY = 0.5

HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# =====================
# 数据文件路径
# =====================

INPUT_FILE = PROJECT_ROOT / "销量.xlsx"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "comic_sales_complete.xlsx"

DEFAULT_DATA_FILE = INPUT_FILE

ENRICHED_DATA_FILE = OUTPUT_FILE

# =====================
# 日志与缓存
# =====================

LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "comic_pipeline.log"

CACHE_DB = PROJECT_ROOT / "data" / "cache.db"
CACHE_DB.parent.mkdir(parents=True, exist_ok=True)

# =====================
# 富化字段
# =====================

ENRICHED_FIELDS = [
    "Writer",
    "Artist",
    "Awards",
    "Main_Character",
    "Semantic_Tags",
    "Comic_Type",
    "Publication_Status",
    "Universe",
    "Franchise",
    "Character",
    "Writer_Source",
    "Artist_Source"
]

# =====================
# 标题翻译
# =====================

TITLE_TRANSLATIONS = {
    "侦探漫画": "Detective Comics",
    "再生侠": "Spawn",
    "蜘蛛侠": "Spider-Man",
    "蝙蝠侠": "Batman",
    "超人": "Superman",
    "复仇者联盟": "Avengers",
    "X战警": "X-Men",
    "神奇女侠": "Wonder Woman",
    "正义联盟": "Justice League",
    "黑袍纠察队": "The Boys",
    "守望者": "Watchmen",
    "沙人": "Sandman",
    "传奇": "Saga"
}

# =====================
# 创作者回退
# =====================

FALLBACK_CREATORS = {
    "spider-man": {
        "writer": "Dan Slott",
        "artist": "Humberto Ramos"
    },
    "batman": {
        "writer": "Scott Snyder",
        "artist": "Greg Capullo"
    },
    "superman": {
        "writer": "Geoff Johns",
        "artist": "Gary Frank"
    },
    "avengers": {
        "writer": "Brian Michael Bendis",
        "artist": "John Romita Jr."
    },
    "x-men": {
        "writer": "Chris Claremont",
        "artist": "Jim Lee"
    }
}


KNOWN_CORRECTIONS = {
    ("detective comics", "1000"): {
        "Writer": "Peter J. Tomasi",
        "Artist": "Doug Mahnke",
        "Main_Character": "Batman",
        "Franchise": "Detective Comics"
    },

    ("spawn", "300"): {
        "Writer": "Todd McFarlane",
        "Artist": "Todd McFarlane",
        "Main_Character": "Spawn",
        "Franchise": "Spawn"
    }
}