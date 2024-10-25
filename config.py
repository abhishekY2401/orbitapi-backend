from pydantic import BaseSettings


class Settings(BaseSettings):
    api_prefix = "/api"

    class Config:
        env_file = ".env"


settings = Settings()
