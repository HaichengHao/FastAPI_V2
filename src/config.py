from pydantic_settings import BaseSettings, SettingsConfigDict


class MYSettings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALOGRITHM: str
    REDIS_HOST: str="localhost"
    REDIS_PORT: int=65522
    DOMAIN_NAME:str="localhost:8088"
    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore'
    )


    #tips:下面是邮件服务所需
    MAIL_USERNAME:str
    MAIL_PASSWORD:str
    MAIL_SERVER:str
    MAIL_PORT:int
    MAIL_FROM:str
    MAIL_STARTTLS:bool
    MAIL_SSL_TLS:bool
    MAIL_FROM_NAME:str
    USE_CREDENTIALS:bool
    VALIDATE_CERTS:bool

project_settings = MYSettings()
