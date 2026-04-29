from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql://neondb_owner:npg_4bOYPUQ3zKCw@ep-patient-hill-amfp2sc9-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # App
    PROJECT_NAME: str = "TotalFit API"
    API_V1_STR: str = "/api/v1"


settings = Settings()
