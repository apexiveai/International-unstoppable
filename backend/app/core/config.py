from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Apexive Community API"
    database_url: str

    frontend_url: str = "https://www.apexiveai.com"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Apexive Community"
    email_enabled: bool = False

    jwt_secret: str = "CHANGE_THIS_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    didit_api_key: str = ""
    didit_workflow_id: str = ""
    didit_api_url: str = "https://verification.didit.me/v3/session/"
    didit_status_url: str = "https://verification.didit.me/v3/session/{session_id}/"
    didit_callback_url: str = ""

    embedding_api_key: str = ""
    embedding_api_url: str = "https://api.openai.com/v1/embeddings"
    embedding_model: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )


settings = Settings()