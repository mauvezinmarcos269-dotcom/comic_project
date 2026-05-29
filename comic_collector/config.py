import os

# ==========================================
# ComicVine API
# ==========================================

COMICVINE_API_KEY = (
    "a610d7acad28d37c0a77e0ef1107cf5ac35fb17e"
)

# ==========================================
# 请求配置
# ==========================================

MAX_CONCURRENT_REQUESTS = 5

REQUEST_TIMEOUT = 20

RETRY_TIMES = 3

REQUEST_DELAY = 0.2

# ==========================================
# User-Agent
# ==========================================

HEADERS = {

    "User-Agent":
        "ComicResearchBot/1.0"
}

# ==========================================
# 输入输出文件
# ==========================================

INPUT_FILE = "销量.xlsx"

OUTPUT_DIR = "outputs"

OUTPUT_FILE = (
    f"{OUTPUT_DIR}/"
    "comic_sales_2010_2019_complete.xlsx"
)

# ==========================================
# 日志目录
# ==========================================

LOG_DIR = "data/logs"

LOG_FILE = (
    f"{LOG_DIR}/collector.log"
)

# ==========================================
# 数据缓存目录
# ==========================================

CACHE_DIR = "data/cache"

# ==========================================
# 自动创建目录
# ==========================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

os.makedirs(
    LOG_DIR,
    exist_ok=True
)

os.makedirs(
    CACHE_DIR,
    exist_ok=True
)

# ==========================================
# 默认缺失值
# ==========================================

DEFAULT_WRITER = "Unknown"

DEFAULT_ARTIST = "Unknown"

DEFAULT_AWARDS = "None"

DEFAULT_CHARACTER = "Unknown"

DEFAULT_RELEASE_YEAR = "Unknown"

DEFAULT_TAGS = "General"

DEFAULT_DESCRIPTION = "No Description"

DEFAULT_GENRE = "Comic"

# ==========================================
# AI 语义标签默认规则
# ==========================================

DEFAULT_TAG_RULES = {

    "Batman": [
        "Dark",
        "Detective",
        "Gothic"
    ],

    "Spider-Man": [
        "Superhero",
        "Teen Hero"
    ],

    "Avengers": [
        "Team-Up",
        "Event"
    ],

    "X-Men": [
        "Mutant",
        "Team-Up"
    ],

    "Venom": [
        "Anti-Hero",
        "Symbiote"
    ],

    "Deadpool": [
        "Comedy",
        "Violence"
    ],

    "Thor": [
        "Mythology",
        "Cosmic"
    ],

    "Guardians": [
        "Cosmic",
        "Sci-Fi"
    ],

    "Watchmen": [
        "Dark",
        "Political"
    ],

    "Sandman": [
        "Fantasy",
        "Horror"
    ]
}

# ==========================================
# Awards 映射
# ==========================================

AWARD_MAP = {

    "Saga":
        "Eisner Award",

    "Watchmen":
        "Hugo Award",

    "Sandman":
        "World Fantasy Award",

    "Maus":
        "Pulitzer Prize",

    "Monstress":
        "Harvey Award"
}

# ==========================================
# 支持出版社
# ==========================================

SUPPORTED_PUBLISHERS = [

    "Marvel",

    "DC",

    "Image",

    "Dark Horse",

    "Boom Studios",

    "IDW",

    "Dynamite",

    "Valiant"
]

# ==========================================
# 系统版本
# ==========================================

APP_NAME = (
    "Ultimate Comic Dataset Collector"
)

VERSION = "2.0"

# ==========================================
# Debug
# ==========================================

DEBUG = True

