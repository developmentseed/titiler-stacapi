

Goal: Support multiple STAC API endpoints 

requirements: titiler.stacapi


```python
"""TiTiler+stacapi FastAPI application."""

from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

import jinja2
import pystac
import rasterio
from fastapi import FastAPI, Path, Query
from fastapi import __version__ as fastapi_version
from fastapi.responses import ORJSONResponse
from pydantic import __version__ as pydantic_version
from rio_tiler import __version__ as rio_tiler_version
from starlette import __version__ as starlette_version
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from titiler.core import __version__ as titiler_version
from titiler.core.dependencies import AssetsBidxExprParams, DefaultDependency
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import (
    AlgorithmFactory,
    ColorMapFactory,
    MultiBaseTilerFactory,
    TMSFactory,
)
from titiler.core.middleware import CacheControlMiddleware
from titiler.core.models.OGC import Conformance, Landing
from titiler.core.utils import accept_media_type, create_html_response, update_openapi
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.mosaic.factory import MosaicTilerFactory
from titiler.stacapi import __version__ as titiler_stacapi_version
from titiler.stacapi.backend import STACAPIBackend
from titiler.stacapi.dependencies import (
    APIParams,
    CollectionSearch,
    STACAPIExtensionParams,
    get_stac_item,
)
from titiler.stacapi.enums import MediaType
from titiler.stacapi.errors import STACAPI_STATUS_CODES
from titiler.stacapi.reader import SimpleSTACReader, STACAPIReader
from titiler.stacapi.settings import ApiSettings

settings = ApiSettings()

# custom template directory
templates_location: list[Any] = (
    [jinja2.FileSystemLoader(settings.template_directory)]
    if settings.template_directory
    else []
)
templates_location.append(jinja2.PackageLoader("titiler.stacapi", "templates"))
templates_location.append(jinja2.PackageLoader("titiler.core", "templates"))

jinja2_env = jinja2.Environment(
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    loader=jinja2.ChoiceLoader(templates_location),
)
templates = Jinja2Templates(env=jinja2_env)

# NOTE: STAC API CATALOGS
catalog = {
    "catalog1": "https://stac.eoapi.dev/",
    "catalog2": "{url for catalog 2}",
}


@dataclass(init=False)
class BackendParams(DefaultDependency):
    """backend parameters."""

    api_params: APIParams = field(init=False)

    def __init__(
        self,
        request: Request,
        catalog_id: Annotated[
            Literal["catalog1", "catalog2"],
            Path(description="Catalog"),
        ],
    ):
        """Initialize BackendParams"""
        self.api_params = APIParams(
            url=request.app.state.catalog[catalog_id],
            # NOTE: you can add headers here
        )


def ItemIdParams(
    request: Request,
    catalog_id: Annotated[
        Literal["catalog1", "catalog2"],
        Path(description="Catalog"),
    ],
    collection_id: Annotated[
        str,
        Path(description="STAC Collection Identifier"),
    ],
    item_id: Annotated[str, Path(description="STAC Item Identifier")],
) -> pystac.Item:
    """STAC Item dependency for the MultiBaseTilerFactory."""
    return get_stac_item(
        request.app.state.catalog[catalog_id],
        collection_id,
        item_id,
        # NOTE: you can add headers here
        headers={},
    )


app = FastAPI(
    title=settings.name,
    openapi_url="/api",
    docs_url="/api.html",
    description="""Connect titiler to STAC APIs.""",
    version=titiler_stacapi_version,
    root_path=settings.root_path,
)

# Fix OpenAPI response header for OGC Common compatibility
update_openapi(app)

# Create catalog store
app.state.catalog = catalog

add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, STACAPI_STATUS_CODES)
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

APP_CONFORMS_TO = {
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/html",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
}

###############################################################################
# STAC COLLECTION Endpoints
collection = MosaicTilerFactory(
    path_dependency=CollectionSearch,
    backend=STACAPIBackend,
    backend_dependency=BackendParams,
    dataset_reader=SimpleSTACReader,
    assets_accessor_dependency=STACAPIExtensionParams,
    optional_headers=[],
    layer_dependency=AssetsBidxExprParams,
    router_prefix="/catalogs/{catalog_id}/collections/{collection_id}",
    add_viewer=True,
    templates=templates,
)
app.include_router(
    collection.router,
    tags=["STAC Collection"],
    prefix="/catalogs/{catalog_id}/collections/{collection_id}",
)
APP_CONFORMS_TO.update(collection.conforms_to)

###############################################################################
# STAC Item Endpoints
stac = MultiBaseTilerFactory(
    reader=STACAPIReader,
    path_dependency=ItemIdParams,
    router_prefix="/catalogs/{catalog_id}/collections/{collection_id}/items/{item_id}",
    add_viewer=True,
    templates=templates,
)
app.include_router(
    stac.router,
    tags=["STAC Item"],
    prefix="/catalogs/{catalog_id}/collections/{collection_id}/items/{item_id}",
)
APP_CONFORMS_TO.update(stac.conforms_to)


###############################################################################
# Tiling Schemes Endpoints
tms = TMSFactory(templates=templates)
app.include_router(tms.router, tags=["OGC TileMatrix Schemes"])
APP_CONFORMS_TO.update(tms.conforms_to)

###############################################################################
# Algorithms Endpoints
algorithms = AlgorithmFactory(templates=templates)
app.include_router(algorithms.router, tags=["Algorithms"])
APP_CONFORMS_TO.update(algorithms.conforms_to)

###############################################################################
# Colormaps endpoints
cmaps = ColorMapFactory(templates=templates)
app.include_router(cmaps.router, tags=["ColorMaps"])
APP_CONFORMS_TO.update(cmaps.conforms_to)


###############################################################################
# Landing page
@app.get(
    "/",
    response_model=Landing,
    response_model_exclude_none=True,
    response_class=ORJSONResponse,
    responses={
        200: {
            "content": {
                "text/html": {},
                "application/json": {},
            }
        },
    },
    operation_id="getLandingPage",
    summary="landing page",
    tags=["Landing Page"],
)
def landing(
    request: Request,
    f: Annotated[
        Literal["html", "json"] | None,
        Query(
            description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
        ),
    ] = None,
):
    """The landing page provides links to the API definition, the conformance statements and to the feature collections in this dataset."""
    data = {
        "title": "TiTiler-STACAPI",
        "description": "A modern dynamic tile server built on top of FastAPI and Rasterio/GDAL.",
        "links": [
            {
                "title": "Landing page",
                "href": str(request.url_for("landing")),
                "type": "text/html",
                "rel": "self",
            },
            {
                "title": "The API definition (JSON)",
                "href": str(request.url_for("openapi")),
                "type": "application/vnd.oai.openapi+json;version=3.0",
                "rel": "service-desc",
            },
            {
                "title": "The API documentation",
                "href": str(request.url_for("swagger_ui_html")),
                "type": "text/html",
                "rel": "service-doc",
            },
            {
                "title": "Conformance Declaration",
                "href": str(request.url_for("conformance")),
                "type": "text/html",
                "rel": "http://www.opengis.net/def/rel/ogc/1.0/conformance",
            },
            {
                "title": "List of Available TileMatrixSets",
                "href": str(request.url_for("tilematrixsets")),
                "type": "application/json",
                "rel": "http://www.opengis.net/def/rel/ogc/1.0/tiling-schemes",
            },
            {
                "title": "List of Available Algorithms",
                "href": str(request.url_for("available_algorithms")),
                "type": "application/json",
                "rel": "data",
            },
            {
                "title": "List of Available ColorMaps",
                "href": str(request.url_for("available_colormaps")),
                "type": "application/json",
                "rel": "data",
            },
            {
                "title": "TiTiler-STACAPI Documentation (external link)",
                "href": "https://developmentseed.org/titiler-stacapi/",
                "type": "text/html",
                "rel": "doc",
            },
            {
                "title": "TiTiler-STACAPI source code (external link)",
                "href": "https://github.com/developmentseed/titiler-stacapi",
                "type": "text/html",
                "rel": "doc",
            },
        ],
    }

    if f:
        output_type = MediaType[f]
    else:
        accepted_media = [MediaType.html, MediaType.json]
        output_type = (
            accept_media_type(request.headers.get("accept", ""), accepted_media)
            or MediaType.json
        )

    if output_type == MediaType.html:
        return create_html_response(
            request,
            data,
            title="TiTiler-STACAPI",
            template_name="landing",
            templates=templates,
        )

    return data


@app.get(
    "/conformance",
    response_model=Conformance,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "text/html": {},
                "application/json": {},
            }
        },
    },
    tags=["OGC Common"],
)
def conformance(
    request: Request,
    f: Annotated[
        Literal["html", "json"] | None,
        Query(
            description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
        ),
    ] = None,
):
    """Conformance classes.

    Called with `GET /conformance`.

    Returns:
        Conformance classes which the server conforms to.

    """
    data = {"conformsTo": sorted(APP_CONFORMS_TO)}

    if f:
        output_type = MediaType[f]
    else:
        accepted_media = [MediaType.html, MediaType.json]
        output_type = (
            accept_media_type(request.headers.get("accept", ""), accepted_media)
            or MediaType.json
        )

    if output_type == MediaType.html:
        return create_html_response(
            request,
            data,
            "conformance",
            title="Conformance",
            templates=templates,
        )

    return data


###############################################################################
# Health Check Endpoint
@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping(request: Request) -> dict:
    """Health check."""
    data = {
        "versions": {
            "titiler": titiler_version,
            "titiler.stacapi": titiler_stacapi_version,
            "rasterio": rasterio.__version__,
            "rio-tiler": rio_tiler_version,
            "gdal": rasterio.__gdal_version__,
            "proj": rasterio.__proj_version__,
            "fastapi": fastapi_version,
            "starlette": starlette_version,
            "pydantic": pydantic_version,
        },
    }

    if settings.debug:
        data["catalog"] = request.app.state.catalog

    return data
```
