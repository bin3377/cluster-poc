import os
from typing import List

from pydantic import BaseModel
from pydantic_settings import BaseSettings, YamlConfigSettingsSource


class OriginCheckConfig(BaseModel):
    enabled: bool
    acceptable_origins: List[str]


class Settings(BaseSettings):
    origin_check: OriginCheckConfig

    model_config = {"yaml_file": f"config/config.{os.getenv('ENV', 'dev')}.yaml"}

    @classmethod
    def settings_customise_sources(cls, settings_cls, *args, **kwargs):
        return (YamlConfigSettingsSource(settings_cls),)


settings = Settings()
