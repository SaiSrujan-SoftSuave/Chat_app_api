from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    HOST: str
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    INVITE_TOKEN_EXPIRE_TIME: int
    JWT_SECRET_KEY: str
    ALGORITHM: str
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore",env_file_encoding="utf-8")



Config = Setting()
