import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 3000))
    APP_DEBUG = os.getenv("APP_DEBUG", "True") == "True"

    BASE_URL = os.getenv("BASE_URL", "/")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 104857600))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 10))
    LOG_ENABLE_FILE = os.getenv("LOG_ENABLE_FILE", "True") == "True"
    LOG_ENABLE_CONSOLE = os.getenv("LOG_ENABLE_CONSOLE", "True") == "True"

    DATABASE_URL = os.getenv(
        "DATABASE_URL", "mysql+pymysql://root:root@localhost:3306/agent"
    )

    IMAGE_STORE = os.getenv("IMAGE_STORE", "local")

    LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")

    all_MiniLM_L6 = os.getenv("all_MiniLM_L6", "")
    MILVUS = os.getenv("MILVUS", "")

    MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME", "")

    RERANK_MODEL_NAME = os.getenv("RERANK_MODEL_NAME", "")

    REASONING_MODEL_ID = os.getenv("REASONING_MODEL_ID", "")
    REASONING_API_KEY = os.getenv("REASONING_API_KEY", "")
    REASONING_BASE_URL = os.getenv("REASONING_BASE_URL", "")
