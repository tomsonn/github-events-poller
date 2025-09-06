from pydantic import AnyHttpUrl, BaseModel
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


class GitHubApiHeaders(BaseModel):
    accept: str = "application/vnd.github+json"


class GitHubApiParams(BaseModel):
    per_page: int = 100


class GitHubApiConfig(BaseSettings):
    url: AnyHttpUrl = AnyHttpUrl("https://api.github.com/events")
    headers: GitHubApiHeaders = GitHubApiHeaders()
    params: GitHubApiParams = GitHubApiParams()
    rate_limit_base: int = 60
    rate_limit_hard: int = 3600

    model_config = SettingsConfigDict(settings_model_config, env_prefix="GH_")


poller_config = PollerConfig()
