from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabasePoolConfig(BaseModel):
    pool_pre_ping: bool = True
    pool_recycle: int = 600


class DatabaseConfig(BaseSettings):
    host: str
    port: str
    user: str
    password: str
    database: str

    pool_config: DatabasePoolConfig

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", env_prefix="DB_"
    )
