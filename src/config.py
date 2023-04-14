from __future__ import annotations

import yaml
from pydantic import BaseModel
from yaml.loader import SafeLoader


class IConfig(BaseModel):
    """
    Base config class
    """
    token: str



def get_config(config_path: str):
    # Open the file and load the file
    with open(config_path) as f:
        data = yaml.load(f, Loader=SafeLoader)
        return IConfig(**data)