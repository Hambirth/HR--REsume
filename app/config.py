"""Application configuration settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # UltraSafe API Configuration
    usf_api_key: str = os.getenv("USF_API_KEY", "")
    usf_base_url: str = os.getenv("USF_BASE_URL", "https://api.us.inc/usf/v1/hiring")
    
    # Application Settings
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Database Settings
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))
    
    # Upload Settings
    upload_dir: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    
    # Model Settings
    chat_model: str = "usf-mini"
    embed_model: str = "usf1-embed"
    rerank_model: str = "usf1-rerank"
    
    # Performance Settings
    api_timeout: int = int(os.getenv("API_TIMEOUT", "60"))  # seconds
    max_concurrent_rankings: int = int(os.getenv("MAX_CONCURRENT_RANKINGS", "3"))
    upload_batch_size: int = int(os.getenv("UPLOAD_BATCH_SIZE", "10"))
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

# Ensure directories exist
Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
