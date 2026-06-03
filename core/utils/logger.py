import logging
from core.config import LOG_FILE

# 自动创建日志存储目录
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    encoding="utf-8"
)

logger = logging.getLogger("ComicResearchPipeline")


