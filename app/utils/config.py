from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ADMIN_SECRET_KEY: str
    APP_NAME: str = "Tom.Camp"
    DB_HOST: str = "localhost"
    DB_NAME: str
    DB_PASSWORD: str
    DB_PORT: int = 5432
    DB_USER: str
    FLASK_DEBUG: bool = True
    FLASK_ENV: str = Field(
        "development", description="Flask environment (development, production, etc.)"
    )
    FLASK_SECRET_KEY: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
