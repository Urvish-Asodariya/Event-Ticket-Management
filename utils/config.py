from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
from typing import List, Union
from pydantic import validator
import os

load_dotenv()

class Settings(BaseSettings):
    MONGODB_URL: str = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.environ.get("DB_NAME", "navratri_pass_db")
    BACKEND_CORS_ORIGINS: List = []
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "your-secret-key-here")
    AES_KEY:str =os.environ.get("AES_KEY")
    IV_KEY:str =os.environ.get("IV_KEY")
    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_TIME: str = os.environ.get("ACCESS_TOKEN_EXPIRE_TIME")
    SMTP_SERVER: str = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.environ.get("SMTP_USERNAME")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD")
    FROM_EMAIL: str = os.environ.get("FROM_EMAIL")

    @validator("BACKEND_CORS_ORIGINS", pre=True, allow_reuse=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    STATIC_FILE :str= "static"

settings = Settings()
