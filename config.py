from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    MONGO_URI: str

    class Config:
        env_file = ".env"


settings = Settings()
