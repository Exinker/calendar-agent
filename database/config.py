from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    database_url: str = Field(..., description="PostgreSQL connection URL")
    encryption_key: str = Field(..., description="Key for encrypting calendar passwords")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"