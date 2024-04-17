"""TiTiler+stacapi FastAPI application."""


from typing import Any, Dict, List, Optional

import jinja2
import pystac
from fastapi import Depends, FastAPI, Path
from fastapi.responses import ORJSONResponse
from fastapi.security import APIKeyHeader
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from typing_extensions import Annotated

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import AlgorithmFactory, MultiBaseTilerFactory, TMSFactory
from titiler.core.middleware import CacheControlMiddleware, LoggerMiddleware
from titiler.core.resources.enums import OptionalHeader
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.stacapi import __version__ as titiler_stacapi_version
from titiler.stacapi import models
from titiler.stacapi.dependencies import (
    APIParams,
    ItemIdParams,
    OutputType,
    STACApiParams,
    get_stac_item,
)
from titiler.stacapi.enums import MediaType
from titiler.stacapi.factory import MosaicTilerFactory, OGCWMTSFactory
from titiler.stacapi.reader import STACReader
from titiler.stacapi.settings import ApiSettings, STACAPISettings
from titiler.stacapi.utils import create_html_response

settings = ApiSettings()
stacapi_config = STACAPISettings()

# custom template directory
templates_location: List[Any] = (
    [jinja2.FileSystemLoader(settings.template_directory)]
    if settings.template_directory
    else []
)
# default template directory
templates_location.append(jinja2.PackageLoader(__package__, "templates"))
templates_location.append(jinja2.PackageLoader("titiler.core", "templates"))

jinja2_env = jinja2.Environment(loader=jinja2.ChoiceLoader(templates_location))
templates = Jinja2Templates(env=jinja2_env)

path_dependency = STACApiParams
item_param = ItemIdParams
if stacapi_config.auth:
    header_scheme = APIKeyHeader(
        name=stacapi_config.auth, description="STAC API Authorization"
    )

    def STACApiParamsAuth(
        request: Request,
        token: Annotated[str, Depends(header_scheme)],
    ) -> APIParams:
        """Return STAC API Parameters."""
        return APIParams(
            api_url=request.app.state.stac_url,
            headers={"Authorization": token},
        )

    path_dependency = STACApiParamsAuth  # type: ignore

    def ItemIdParams(
        collection_id: Annotated[
            str,
            Path(description="STAC Collection Identifier"),
        ],
        item_id: Annotated[str, Path(description="STAC Item Identifier")],
        api_params=Depends(STACApiParamsAuth),
    ) -> pystac.Item:
        """STAC Item dependency for the MultiBaseTilerFactory."""
        return get_stac_item(
            api_params["api_url"],
            collection_id,
            item_id,
            headers=api_params.get("headers", {}),
        )

    item_param = ItemIdParams  # type: ignore


app = FastAPI(
    title=settings.name,
    openapi_url="/api",
    docs_url="/api.html",
    description="""Connect titiler to STAC APIs.

---

**Documentation**: <a href="https://developmentseed.org/titiler-stacapi/" target="_blank">https://developmentseed.org/titiler-stacapi/</a>

**Source Code**: <a href="https://github.com/developmentseed/titiler-stacapi" target="_blank">https://github.com/developmentseed/titiler-stacapi</a>

---
    """,
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

optional_headers = []
if settings.debug:
    app.add_middleware(LoggerMiddleware, headers=True, querystrings=True)
    optional_headers = [OptionalHeader.server_timing, OptionalHeader.x_assets]

###############################################################################
# STAC COLLECTION Endpoints
# Notes:
# - The `path_dependency` is set to `STACApiParams` which define `{collection_id}`
# `Path` dependency and other Query parameters used to construct STAC API Search request.
collection = MosaicTilerFactory(
    path_dependency=path_dependency,
    optional_headers=optional_headers,
    router_prefix="/collections/{collection_id}",
    add_viewer=True,
    templates=templates,
)
app.include_router(
    collection.router, tags=["STAC Collection"], prefix="/collections/{collection_id}"
)

###############################################################################
# STAC Item Endpoints
# Notes: The `MultiBaseTilerFactory` from titiler.core.factory expect a `URL` as query parameter
# but in this project we use a custom `path_dependency=ItemIdParams`, which define `{collection_id}` and `{item_id}` as
# `Path` dependencies. Then the `ItemIdParams` dependency will fetch the STAC API endpoint to get the STAC Item. The Item
# will then be used in our custom `STACReader`.
stac = MultiBaseTilerFactory(
    reader=STACReader,
    path_dependency=item_param,
    optional_headers=optional_headers,
    router_prefix="/collections/{collection_id}/items/{item_id}",
    add_viewer=True,
)
app.include_router(
    stac.router,
    tags=["STAC Item"],
    prefix="/collections/{collection_id}/items/{item_id}",
)

###############################################################################
# OGC WMTS Endpoints
wmts = OGCWMTSFactory(
    path_dependency=path_dependency,
    templates=templates,
)
app.include_router(
    wmts.router,
    tags=["Web Map Tile Service"],
)

###############################################################################
# Tiling Schemes Endpoints
tms = TMSFactory()
app.include_router(tms.router, tags=["Tiling Schemes"])

###############################################################################
# Algorithms Endpoints
algorithms = AlgorithmFactory()
app.include_router(algorithms.router, tags=["Algorithms"])


###############################################################################
# Health Check Endpoint
@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping() -> Dict:
    """Health check."""
    return {"Howdy": "Let's make happy tiles"}


###############################################################################
# Landing page
@app.get(
    "/",
    response_model=models.Landing,
    response_model_exclude_none=True,
    response_class=ORJSONResponse,
    responses={
        200: {
            "content": {
                MediaType.json.value: {},
                MediaType.html.value: {},
            }
        },
    },
    operation_id="getLandingPage",
    summary="landing page",
    tags=["Landing Page"],
)
def landing(
    request: Request,
    output_type: Annotated[Optional[MediaType], Depends(OutputType)] = None,
):
    """The landing page provides links to the API definition, the conformance statements and to the feature collections in this dataset."""
    data = models.Landing(
        title=settings.name,
        links=[
            models.Link(
                title="Landing Page",
                href=str(request.url_for("landing")),
                type=MediaType.html,
                rel="self",
            ),
            models.Link(
                title="the API definition (JSON)",
                href=str(request.url_for("openapi")),
                type=MediaType.openapi30_json,
                rel="service-desc",
            ),
            models.Link(
                title="the API documentation",
                href=str(request.url_for("swagger_ui_html")),
                type=MediaType.html,
                rel="service-doc",
            ),
            models.Link(
                title="STAC-API endpoint (external link)",
                href=request.app.state.stac_url,
                type=MediaType.json,
                rel="data",
            ),
            models.Link(
                title="TiTiler-STACAPI Documentation (external link)",
                href="https://developmentseed.org/titiler-stacapi/",
                type=MediaType.html,
                rel="doc",
            ),
            models.Link(
                title="TiTiler-STACAPI source code (external link)",
                href="https://github.com/developmentseed/titiler-stacapi",
                type=MediaType.html,
                rel="doc",
            ),
        ],
    )

    if output_type == MediaType.html:
        return create_html_response(
            request,
            data.model_dump(exclude_none=True, mode="json"),
            templates=templates,
            template_name="landing",
        )

    return data
