

Goal: add `Authentication` forwarding to the `/wmts` endpoints

requirements: titiler.stacapi


```python
"""TiTiler+stacapi FastAPI application."""

from dataclasses import dataclass, field

from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from typing_extensions import Annotated

import morecantile
from titiler.core.dependencies import DefaultDependency
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.middleware import CacheControlMiddleware
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.stacapi import __version__ as titiler_stacapi_version
from titiler.stacapi.dependencies import APIParams
from titiler.stacapi.factory import OGCEndpointsFactory
from titiler.stacapi.settings import ApiSettings, STACAPISettings

settings = ApiSettings()
stacapi_config = STACAPISettings()


header_scheme = APIKeyHeader(name="Authorization", description="STAC API Authorization")


@dataclass(init=False)
class BackendParams(DefaultDependency):
    """backend parameters."""

    api_params: APIParams = field(init=False)

    def __init__(self, request: Request, token: Annotated[str, Depends(header_scheme)]):
        """Initialize BackendParams

        Note: Because we don't want `api_params` to appear in the documentation we use a dataclass with a custom `__init__` method.
        FastAPI will use the `__init__` method but will exclude Request in the documentation making `api_params` an invisible dependency.
        """
        self.api_params = APIParams(
            url=request.app.state.stac_url,
            headers={"Authorization": token},
        )


app = FastAPI(
    title=settings.name,
    openapi_url="/api",
    docs_url="/api.html",
    description="""Connect titiler to STAC APIs.""",
    version=titiler_stacapi_version,
    root_path=settings.root_path,
)

# We store the STAC API url in the application state
app.state.stac_url = stacapi_config.stac_api_url

add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)

# Set all CORS enabled origins
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

app.add_middleware(CacheControlMiddleware, cachecontrol=settings.cachecontrol)

webmerc = morecantile.tms.get("WebMercatorQuad").model_dump()
webmerc["id"] = "EPSG3857"
supported_tms = morecantile.TileMatrixSets({"EPSG3857": morecantile.TileMatrixSet.model_validate(webmerc)})

###############################################################################
# OGC WMTS Endpoints
wmts = OGCEndpointsFactory(
    backend_dependency=BackendParams,
    supported_tms=supported_tms,
)

app.include_router(wmts.router, tags=["Web Map Tile Service"])

```
