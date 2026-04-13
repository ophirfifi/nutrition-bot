from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str
    telegram_webhook_secret: str

    # Anthropic
    anthropic_api_key: str

    # Firebase
    # One of these two must be set:
    firebase_credentials_path: str = ""     # path to service account JSON (local dev)
    firebase_credentials_base64: str = ""   # base64-encoded JSON (Railway / production)
    firebase_project_id: str

    # Hosting
    webhook_base_url: str  # https://your-domain.railway.app (no trailing slash)

    # Admin
    admin_secret_token: str = ""  # shared secret for /api/admin/* endpoints

    # App
    debug: bool = False
    skip_telegram: bool = False  # set True locally when Telegram API is unreachable


settings = Settings()
