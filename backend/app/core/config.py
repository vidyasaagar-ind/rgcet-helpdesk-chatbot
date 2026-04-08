from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_VECTOR_STORE_PATH = BASE_DIR / "data" / "vector_store"

class Settings(BaseSettings):
    app_name: str = "RGCET Help Desk Backend"
    environment: str = "development"
    port: int = 8080

    use_gemini: bool = True
    gemini_api_key: str = "placeholder_key"
    model_name: str = "models/gemini-2.0-flash"
    top_k_results: int = 4
    similarity_threshold: float = 0.65
    embedding_model: str = "models/embedding-001"
    chroma_db_path: str = str(DEFAULT_VECTOR_STORE_PATH)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", protected_namespaces=())

    @property
    def resolved_chroma_db_path(self) -> str:
        configured_path = Path(self.chroma_db_path)
        if not configured_path.is_absolute():
            configured_path = BASE_DIR / configured_path

        if configured_path.exists():
            return str(configured_path)

        return str(DEFAULT_VECTOR_STORE_PATH)

# Initialize global config
settings = Settings()
