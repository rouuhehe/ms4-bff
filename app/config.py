from pydantic_settings import BaseSettings
from pydantic import AnyUrl

class Settings(BaseSettings):
    MS1_URL: AnyUrl
    MS2_URL: AnyUrl
    MS3_URL: AnyUrl
    REDIS_URL: str = "redis://redis:6379/0"
    CACHE_TTL: int = 30
    HTTP_TIMEOUT_SECONDS: int = 5
    RETRIES: int = 3
    CIRCUIT_FAIL_MAX: int = 5
    CIRCUIT_RESET_TIMEOUT: int = 20
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"