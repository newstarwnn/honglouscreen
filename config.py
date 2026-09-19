"""后端项目基础配置。"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TEXT_DATA_DIR = BASE_DIR / "txt_data"
TEXT_SOURCE_PATH = TEXT_DATA_DIR / "红楼梦.txt"
DEFAULT_ENCODING = "utf-8"

API_PREFIX = "/api"
CACHE_TTL_SECONDS = 60 * 60 * 24
