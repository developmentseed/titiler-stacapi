"""API settings."""

from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from typing_extensions import Annotated


class ApiSettings(BaseSettings):
    """API settings"""

    name: str = "titiler-stacapi"
    cors_origins: str = "*"
    cachecontrol: str = "public, max-age=3600"
    root_path: str = ""
    debug: bool = False
    template_directory: Optional[str] = None

    model_config = {
        "env_prefix": "TITILER_STACAPI_API_",
        "env_file": ".env",
        "extra": "ignore",
    }

    @field_validator("cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]


class CacheSettings(BaseSettings):
    """Cache settings"""

    # TTL of the cache in seconds
    ttl: int = 300

    # Maximum size of the cache in Number of element
    maxsize: int = 512

    # Whether or not caching is enabled
    disable: bool = False

    model_config = {
        "env_prefix": "TITILER_STACAPI_CACHE_",
        "env_file": ".env",
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def check_enable(self):
        """Check if cache is disabled."""
        if self.disable:
            self.ttl = 0
            self.maxsize = 0

        return self


class RetrySettings(BaseSettings):
    """Retry settings"""

    # Total number of retries to allow.
    retry: Annotated[int, Field(ge=0)] = 3

    # A backoff factor to apply between attempts after the second try
    retry_factor: Annotated[float, Field(ge=0.0)] = 0.0

    model_config = {
        "env_prefix": "TITILER_STACAPI_API_",
        "env_file": ".env",
        "extra": "ignore",
    }


class STACAPISettings(BaseSettings):
    """STAC API settings"""

    stac_api_url: str
    mspc_default_api_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"

    model_config = {
        "env_prefix": "TITILER_STACAPI_",
        "env_file": ".env",
        "extra": "ignore",
    }


class STACSettings(BaseSettings):
    """STAC API settings"""

    model_config = {
        "env_prefix": "TITILER_STACAPI_",
        "env_file": ".env",
        "extra": "ignore",
    }
