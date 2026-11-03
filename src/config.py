from celery import Celery
from pydantic_settings import BaseSettings, SettingsConfigDict


class MYSettings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALOGRITHM: str
    REDIS_HOST: str="localhost"
    REDIS_PORT: int=65522
    DOMAIN_NAME:str="127.0.0.1:8088"
    REDIS_URL:str #新增全redis链接方便celery设置
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

broker_url = project_settings.REDIS_URL
result_backend = project_settings.REDIS_URL  #tips:设置结果后端
# broker_connection_retry_on_startup = True
#这里还是用到一个设置,可以将retry_on_startup设置为True,那么就是将对应的启动时重启功能打开