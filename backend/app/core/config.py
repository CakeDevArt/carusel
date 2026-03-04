from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_URL: str = ""
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "carousels"
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-5-nano-2025-08-07"
    APP_API_KEY: str = ""
    BACKEND_PUBLIC_URL: str = "http://localhost:8090"

    class Config:
        env_file = ".env"


settings = Settings()
