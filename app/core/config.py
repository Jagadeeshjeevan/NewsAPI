from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "zsttrxnv_digiNews"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    SECRET_KEY: str = "change-this-secret-key-to-something-long"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    GOOGLE_CLIENT_ID: str = ""

    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    FIREBASE_ENABLED: bool = False
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"
    GOOGLE_APPLICATION_CREDENTIALS: str = "gcp-credentials.json"

    OPENAI_API_KEY: str = ""

    AUDIO_STORAGE_PATH: str = "/storage/audio"
    IMAGE_STORAGE_PATH: str = "/storage/images"
    BASE_URL: str = "http://localhost:8000"

    LOG_ENABLED: bool = False
    LOG_PATH: str = "/home/zsttrxnv/logs/diginews_app.log"
    LOG_LEVEL: str = "ERROR"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
