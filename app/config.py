from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:1710058327@localhost:5432/randomusers"
    RANDOM_USER_API: str = "https://randomuser.me/api/"

settings = Settings()