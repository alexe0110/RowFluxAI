from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PGSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='PG_', extra='ignore')

    user: str
    password: SecretStr
    db: str
    host: str
    port: int = Field(5432)

    @property
    def dsn(self) -> str:
        return PostgresDsn.build(
            scheme='postgresql',
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            path=self.db,
        ).unicode_string()


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='OPENAI_', extra='ignore')

    api_key: str = ''


class AnthropicSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='ANTHROPIC_', extra='ignore')

    api_key: str = ''



class YandexSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='YANDEX_', extra='ignore')

    api_key: str = ''
    folder_id: str = ''


class PipelineSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='PIPELINE_', extra='ignore')

    batch_commit_size: int = 10
    max_retries: int = 3
    log_file: str = 'pipeline.log'
