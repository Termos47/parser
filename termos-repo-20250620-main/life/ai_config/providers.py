# ai_config/providers.py
from enum import Enum
from pydantic import BaseModel

class AIProvider(str, Enum):
    YANDEX_GPT = "yandex"
    OPENAI = "openai"

class ProviderConfig(BaseModel):
    active_provider: AIProvider = AIProvider.YANDEX_GPT
    yandex: dict = {}
    openai: dict = {}