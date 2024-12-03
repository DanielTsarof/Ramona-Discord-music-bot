from __future__ import annotations
from typing import Literal

import yaml
from pydantic import BaseModel
from yaml.loader import SafeLoader


class General(BaseModel):
    discord_token: str
    llm_api_key: str
    youtube_token: str


class Speech(BaseModel):
    provider: Literal['openai', 'ai21']
    model: str
    temperature: float
    ans_max_length: int
    max_tokens: int
    prompt: str


class IConfig(BaseModel):
    """
    Base config class
    """
    general: General
    speech: Speech


def get_config(config_path: str):
    # Open the file and load the file
    with open(config_path, encoding='utf-8') as f:
        data = yaml.load(f, Loader=SafeLoader)
        return IConfig(**data)

config = get_config('config.yaml')
