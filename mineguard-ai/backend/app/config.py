from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Server
    APP_NAME: str = "MineGuard AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500,http://127.0.0.1:8080,http://localhost:8080"

    # Database
    DATABASE_URL: str = "sqlite:///./mineguard.db"

    # ML
    MODEL_PATH: str = "./data/models/risk_model.pkl"

    # RAG
    VECTOR_DB_PATH: str = "./data/vectordb"
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDER_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 5
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
