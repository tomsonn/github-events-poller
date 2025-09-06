from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


settings_model_config = SettingsConfigDict(
    env_file=".env", env_file_encoding="utf-8", extra="ignore"
)


class DatabasePoolConfig(BaseModel):
    pool_pre_ping: bool = True
    pool_recycle: int = 600


class DatabaseConfig(BaseSettings):
    host: str
    port: str
    user: str
    password: str
    database: str

    pool_config: DatabasePoolConfig = DatabasePoolConfig()

    model_config = SettingsConfigDict(settings_model_config, env_prefix="DB_")


class PollerConfig(BaseSettings):
    queue_size: int = 1000
    workers_count: int = 2

    model_config = SettingsConfigDict(settings_model_config, env_prefix="POLLER_")


poller_config = PollerConfig()
