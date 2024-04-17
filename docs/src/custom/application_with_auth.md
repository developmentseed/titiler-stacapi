

Goal: add `Authentication` forwarding to the `/wmts` endpoints

requirements: titiler.stacapi


```python
"""TiTiler+stacapi FastAPI application."""


from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from typing_extensions import Annotated

import morecantile
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.middleware import CacheControlMiddleware
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.stacapi import __version__ as titiler_stacapi_version
from titiler.stacapi.dependencies import APIParams
from titiler.stacapi.factory import OGCWMTSFactory
from titiler.stacapi.settings import ApiSettings, STACAPISettings

settings = ApiSettings()
stacapi_config = STACAPISettings()


header_scheme = APIKeyHeader(name="Authorization", description="STAC API Authorization")


def STACApiParamsAuth(
    request: Request,
    token: Annotated[str, Depends(header_scheme)],
) -> APIParams:
    """Return STAC API Parameters."""
    return APIParams(
        api_url=request.app.state.stac_url,
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

webmerc = morecantile.tms.get("WebMercatorQuad")
webmerc.id = "EPSG:3857"
supported_tms = morecantile.TileMatrixSets({"EPSG:3857": webmerc})

###############################################################################
# OGC WMTS Endpoints
wmts = OGCWMTSFactory(
    path_dependency=STACApiParamsAuth,
    supported_tms=supported_tms,
)

app.include_router(
    wmts.router,
    tags=["Web Map Tile Service"],
)

```
