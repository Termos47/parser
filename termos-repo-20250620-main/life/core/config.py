# core/config.py
import os
from dotenv import load_dotenv
from pydantic import BaseSettings, AnyUrl

class BaseConfig(BaseSettings):
    DEBUG: bool = False
    RABBITMQ_URL: AnyUrl = "amqp://localhost:5672"
    
    PROJECT1_ENABLED: bool = True
    PROJECT2_ENABLED: bool = False
    PROJECT3_ENABLED: bool = False
    
    TG_BOT_TOKEN: str = ""
    TG_CHANNEL_ID: str = ""
    
    YANDEX_API_KEY: str = ""
    YANDEX_FOLDER_ID: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

def load_config():
    load_dotenv()
    return BaseConfig()