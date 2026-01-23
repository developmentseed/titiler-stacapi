"""Custom MosaicTiler Factory for TiTiler-STACAPI Mosaic Backend."""

import datetime as python_datetime
import json
import os
from copy import copy
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Type, cast
from urllib.parse import urlencode

import jinja2
import rasterio
from attrs import define, field
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from fastapi import Depends, HTTPException, Path
from fastapi.dependencies.utils import get_dependant, request_params_to_args
from morecantile import tms as morecantile_tms
from morecantile.defaults import TileMatrixSets
from pystac_client.stac_api_io import StacApiIO
from rasterio.crs import CRS
from rasterio.transform import xy as rowcol_to_coords
from rasterio.warp import transform as transform_points
from rio_tiler.constants import MAX_THREADS
from rio_tiler.models import ImageData
from rio_tiler.mosaic.methods.base import MosaicMethodBase
from rio_tiler.types import ColorMapType
from rio_tiler.utils import CRS_to_uri
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from typing_extensions import Annotated
from urllib3 import Retry

from titiler.core.algorithm import BaseAlgorithm
from titiler.core.algorithm import algorithms as available_algorithms
from titiler.core.dependencies import (
    AssetsBidxExprParams,
    ColorMapParams,
    DatasetParams,
    DefaultDependency,
    ImageRenderingParams,
    TileParams,
)
from titiler.core.factory import BaseFactory, img_endpoint_params
from titiler.core.resources.enums import ImageType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse
from titiler.core.utils import render_image, tms_limits
from titiler.extensions.wms import OverlayMethod
from titiler.mosaic.factory import PixelSelectionParams
from titiler.stacapi.backend import STACAPIBackend
from titiler.stacapi.dependencies import (
    APIParams,
    BackendParams,
    Search,
    SearchParams,
    STACAPIExtensionParams,
)
from titiler.stacapi.models import FeatureInfo, LayerDict
from titiler.stacapi.pystac import Client
from titiler.stacapi.reader import SimpleSTACReader
from titiler.stacapi.settings import CacheSettings, RetrySettings

cache_config = CacheSettings()
retry_config = RetrySettings()

ttl_cache = TTLCache(maxsize=cache_config.maxsize, ttl=cache_config.ttl)  # type: ignore

MOSAIC_THREADS = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))
MOSAIC_STRICT_ZOOM = str(os.getenv("MOSAIC_STRICT_ZOOM", False)).lower() in [
    "true",
    "yes",
]

jinja2_env = jinja2.Environment(
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    loader=jinja2.ChoiceLoader(
        [
            jinja2.PackageLoader(__package__, "templates"),
            jinja2.PackageLoader("titiler.core", "templates"),
        ]
    ),
)
DEFAULT_TEMPLATES = Jinja2Templates(env=jinja2_env)


def get_dependency_params(*, dependency: Callable, query_params: Dict) -> Any:
    """Check QueryParams for Query dependency.

    1. `get_dependant` is used to get the query-parameters required by the `callable`
    2. we use `request_params_to_args` to construct arguments needed to call the `callable`
    3. we call the `callable` and catch any errors

    Important: We assume the `callable` in not a co-routine

    """
    dep = get_dependant(path="", call=dependency)
    if dep.query_params:
        # call the dependency with the query-parameters values
        query_values, _ = request_params_to_args(dep.query_params, query_params)
        return dependency(**query_values)

    return dependency()


class MediaType(str, Enum):
    """Responses Media types for WMTS"""

    tif = "image/tiff; application=geotiff"
    jp2 = "image/jp2"
    png = "image/png"
    jpeg = "image/jpeg"
    jpg = "image/jpg"
    webp = "image/webp"


@cached(  # type: ignore
    ttl_cache,
    key=lambda api_params, supported_tms: hashkey(
        api_params["url"], json.dumps(api_params.get("headers", {}))
    ),
)
def get_layer_from_collections(  # noqa: C901
    api_params: APIParams,
    supported_tms: TileMatrixSets | None = None,
) -> dict[str, LayerDict]:
    """Get Layers from STAC Collections."""
    stac_api_io = StacApiIO(
        max_retries=Retry(
            total=retry_config.retry,
            backoff_factor=retry_config.retry_factor,
        ),
        headers=api_params.get("headers", {}),
    )
    catalog = Client.open(api_params["url"], stac_io=stac_api_io)

    layers = {}
    for collection in catalog.get_collections():
        spatial_extent = collection.extent.spatial
        temporal_extent = collection.extent.temporal

        if "renders" in collection.extra_fields:
            for name, render in collection.extra_fields["renders"].items():
                tilematrixsets: dict[str, tuple[int, int] | None] = render.pop(
                    "tilematrixsets", None
                )
                output_format = render.pop("format", None)
                aggregation = render.pop("aggregation", None)
                title = render.pop("title", None)

                _ = render.pop("minmax_zoom", None)  # Not Used
                _ = render.pop("title", None)  # Not Used

                # see https://github.com/developmentseed/eoAPI-vito/issues/9#issuecomment-2034025021
                render_id = f"{collection.id}_{name}"
                layer = {
                    "id": render_id,
                    "collection": collection.id,
                    "title": title,
                    "bbox": (-180, -90, 180, 90),
                    "style": "default",
                    "render": render,
                }
                if output_format:
                    layer["format"] = output_format

                if spatial_extent:
                    layer["bbox"] = tuple(spatial_extent.bboxes[0])

                if supported_tms:
                    tilematrixsets = tilematrixsets or {
                        tms_id: None for tms_id in supported_tms.list()
                    }

                    layer["tilematrixsets"] = {}
                    for tms_id, zooms in tilematrixsets.items():
                        try:
                            limits = tms_limits(
                                supported_tms.get(tms_id),
                                layer["bbox"],
                                zooms=zooms,
                            )
                            # NOTE: The WMTS spec is contradictory re. the multiplicity
                            # relationships between Layer and TileMatrixSetLink, and
                            # TileMatrixSetLink and tileMatrixSet (URI).
                            # WMTS only support 1 set of limits for a TileMatrixSet
                            layer["tilematrixsets"][tms_id] = (
                                limits if len(tilematrixsets) == 1 else None
                            )
                        except Exception as e:  # noqa
                            pass

                if (
                    "cube:dimensions" in collection.extra_fields
                    and "time" in collection.extra_fields["cube:dimensions"]
                ):
                    layer["time"] = [
                        python_datetime.datetime.strptime(
                            t,
                            "%Y-%m-%dT%H:%M:%SZ",
                        ).strftime("%Y-%m-%d")
                        for t in collection.extra_fields["cube:dimensions"]["time"][
                            "values"
                        ]
                    ]
                elif aggregation and aggregation["name"] == "datetime_frequency":
                    datetime_aggregation = catalog.get_aggregation(
                        collection_id=collection.id,
                        aggregation="datetime_frequency",
                        aggregation_params=aggregation["params"],
                    )
                    layer["time"] = [
                        python_datetime.datetime.strptime(
                            t["key"],
                            "%Y-%m-%dT%H:%M:%S.000Z",
                        ).strftime("%Y-%m-%d")
                        for t in datetime_aggregation
                        if t["frequency"] > 0
                    ]
                elif intervals := temporal_extent.intervals:
                    start_date = intervals[0][0]
                    end_date = (
                        intervals[0][1]
                        if intervals[0][1]
                        else python_datetime.datetime.now(python_datetime.timezone.utc)
                    )

                    layer["time"] = [
                        (start_date + python_datetime.timedelta(days=x)).strftime(
                            "%Y-%m-%d"
                        )
                        for x in range(0, (end_date - start_date).days + 1)
                    ]

                render = layer["render"] or {}

                # special encoding for rescale
                # Per Specification, the rescale entry is a 2d array in form of `[[min, max], [min,max]]`
                # We need to convert this to `['{min},{max}', '{min},{max}']` for titiler dependency
                if rescale := render.pop("rescale", None):
                    rescales = []
                    for r in rescale:
                        if not isinstance(r, str):
                            rescales.append(",".join(map(str, r)))
                        else:
                            rescales.append(r)

                    render["rescale"] = rescales

                # special encoding for ColorMaps
                # Per Specification, the colormap is a JSON object. TiTiler dependency expects a string encoded dict
                if colormap := render.pop("colormap", None):
                    if not isinstance(colormap, str):
                        colormap = json.dumps(colormap)

                    render["colormap"] = colormap

                qs = urlencode(
                    [(k, v) for k, v in render.items() if v is not None],
                    doseq=True,
                )
                layer["query_string"] = str(qs)

                layers[render_id] = {
                    "id": layer["id"],
                    "collection": layer["collection"],
                    "title": layer.get("title"),
                    "bbox": layer["bbox"],
                    "format": layer.get("format"),
                    "style": layer["style"],
                    "render": layer.get("render", {}),
                    "time": layer.get("time"),
                    "query_string": layer["query_string"],
                }

                if tilematrixset := layer.get("tilematrixsets"):
                    layers[render_id]["tilematrixsets"] = tilematrixset

    return cast(dict[str, LayerDict], layers)


@define(kw_only=True)
class OGCEndpointsFactory(BaseFactory):
    """Create /wmts and /wms endpoints"""

    backend: Type[STACAPIBackend] = STACAPIBackend
    # Backend Depencency has the api_params informations
    backend_dependency: Type[BackendParams] = BackendParams

    dataset_reader: Type[SimpleSTACReader] = SimpleSTACReader
    reader_dependency: Type[DefaultDependency] = DefaultDependency

    search_dependency: Callable[..., Search] = SearchParams
    assets_accessor_dependency: Type[DefaultDependency] = STACAPIExtensionParams

    # Because the endpoints should work with STAC Items,
    # the `layer_dependency` define which query parameters are mandatory/optional to `display` images
    # Defaults to `titiler.core.dependencies.AssetsBidxExprParams`, `assets=` or `expression=` is required
    layer_dependency: Type[DefaultDependency] = AssetsBidxExprParams

    # Rasterio Dataset Options (nodata, unscale, resampling, reproject)
    dataset_dependency: Type[DefaultDependency] = DatasetParams

    # The `tile_dependency` define options like `buffer` or `padding`
    # used in Tile/Tilejson/WMTS Dependencies
    tile_dependency: Type[DefaultDependency] = TileParams

    # Post Processing Dependencies (algorithm)
    process_dependency: Callable[..., Optional[BaseAlgorithm]] = (
        available_algorithms.dependency
    )

    # Image rendering Dependencies
    colormap_dependency: Callable[..., Optional[ColorMapType]] = ColorMapParams
    render_dependency: Type[DefaultDependency] = ImageRenderingParams

    pixel_selection_dependency: Callable[..., MosaicMethodBase] = PixelSelectionParams

    # GDAL ENV dependency
    environment_dependency: Callable[..., Dict] = field(default=lambda: {})

    supported_tms: TileMatrixSets = morecantile_tms
    supported_crs: List[str] = field(default_factory=lambda: ["EPSG:4326"])

    optional_headers: List[OptionalHeader] = field(factory=list)

    supported_format: List[str] = field(
        factory=lambda: [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
            "image/jp2",
            "image/tiff; application=geotiff",
        ]
    )

    supported_wmts_version: List[str] = field(factory=lambda: ["1.0.0"])
    supported_wms_version: List[str] = field(
        factory=lambda: ["1.0.0", "1.1.1", "1.3.0"]
    )

    templates: Jinja2Templates = DEFAULT_TEMPLATES

    def get_tile(  # noqa: C901
        self,
        req: Dict,
        layer: LayerDict,
        api_params: APIParams,
    ) -> ImageData:
        """Get Tile Data."""
        layer_time = layer.get("time")
        req_time = req.get("time")
        if layer_time and "time" not in req:
            raise HTTPException(
                status_code=400,
                detail=f"Missing 'TIME' parameters for layer {layer['id']}",
            )

        if layer_time and req_time not in layer_time:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid 'TIME' parameter: {req_time}. Not available.",
            )

        tms_id = req["tilematrixset"]
        if tms_id not in self.supported_tms.list():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid 'TILEMATRIXSET' parameter: {tms_id}. Should be one of {self.supported_tms.list()}.",
            )

        z = int(req["tilematrix"])
        x = int(req["tilecol"])
        y = int(req["tilerow"])

        ###########################################################
        # STAC Query parameter provided by the render extension and QueryParameters
        ###########################################################
        query_params = copy(layer.get("render")) or {}

        if req_time:
            start_datetime = python_datetime.datetime.strptime(
                req_time,
                "%Y-%m-%d",
            ).replace(tzinfo=python_datetime.timezone.utc)
            end_datetime = (
                start_datetime
                + python_datetime.timedelta(days=1)
                - python_datetime.timedelta(
                    milliseconds=1
                )  # prevent inclusion of following day
            )

            query_params["datetime"] = (
                f"{start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            )

        if "color_formula" in req:
            query_params["color_formula"] = req["color_formula"]

        if "expression" in req:
            query_params["expression"] = req["expression"]

        search_query = get_dependency_params(
            dependency=self.search_dependency,
            query_params=query_params,
        )
        search_query["collections"] = [layer["collection"]]

        asset_accessor = get_dependency_params(
            dependency=self.assets_accessor_dependency,
            query_params=query_params,
        )
        tile_params = get_dependency_params(
            dependency=self.tile_dependency,
            query_params=query_params,
        )
        layer_params = get_dependency_params(
            dependency=self.layer_dependency,
            query_params=query_params,
        )
        reader_params = get_dependency_params(
            dependency=self.reader_dependency,
            query_params=query_params,
        )
        dataset_params = get_dependency_params(
            dependency=self.dataset_dependency,
            query_params=query_params,
        )
        pixel_selection = get_dependency_params(
            dependency=self.pixel_selection_dependency,
            query_params=query_params,
        )
        rendering = get_dependency_params(
            dependency=self.render_dependency,
            query_params=query_params,
        )

        tms = self.supported_tms.get(tms_id)
        with self.backend(
            search_query,
            tms=tms,
            reader=self.dataset_reader,
            reader_options={**reader_params.as_dict()},
            api_params=api_params,
        ) as src_dst:
            if MOSAIC_STRICT_ZOOM and (z < src_dst.minzoom or z > src_dst.maxzoom):
                raise HTTPException(
                    400,
                    f"Invalid ZOOM level {z}. Should be between {src_dst.minzoom} and {src_dst.maxzoom}",
                )

            image, _ = src_dst.tile(
                x,
                y,
                z,
                # STAC Query Params
                search_options=asset_accessor.as_dict(),
                pixel_selection=pixel_selection,
                threads=MOSAIC_THREADS,
                **tile_params.as_dict(),
                **layer_params.as_dict(),
                **dataset_params.as_dict(),
            )

            if post_process := get_dependency_params(
                dependency=self.process_dependency,
                query_params=query_params,
            ):
                image = post_process(image)

            if rendering.rescale:
                image.rescale(rendering.rescale)

            if rendering.color_formula:
                image.apply_color_formula(rendering.color_formula)

        return image

    # GetMap: Return an image chip
    def get_map_data(  # noqa: C901
        self,
        req: dict,
        req_keys: set,
        request_type: str,
        layer: LayerDict,
        api_params: APIParams,
        version: str,
    ) -> ImageData:
        """Get Map data."""
        # Required parameters:
        # - LAYERS
        # - STYLES
        # - CRS
        # - BBOX
        # - WIDTH
        # - HEIGHT
        # - FORMAT
        # Optional parameters: TRANSPARENT, BGCOLOR, EXCEPTIONS, TIME, ELEVATION, ...
        intrs = set(req.keys()).intersection(req_keys)
        missing_keys = req_keys.difference(intrs)
        if len(missing_keys) > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Missing '{request_type}' parameters: {missing_keys}",
            )

        if not set(req.keys()).intersection({"crs", "srs"}):
            raise HTTPException(
                status_code=400, detail="Missing 'CRS' or 'SRS parameters."
            )

        crs_value = req.get("crs", req.get("srs"))
        if not crs_value:
            raise HTTPException(status_code=400, detail="Invalid 'CRS' parameter.")

        crs = CRS.from_user_input(crs_value)

        bbox = list(map(float, req["bbox"].split(",")))
        if len(bbox) != 4:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid 'BBOX' parameters: {req['bbox']}. Needs 4 coordinates separated by commas",
            )

        if version == "1.3.0":
            # WMS 1.3.0 is lame and flips the coords of EPSG:4326
            # EPSG:4326 refers to WGS 84 geographic latitude, then longitude.
            # That is, in this CRS the x axis corresponds to latitude, and the y axis to longitude.
            if crs == CRS.from_epsg(4326):
                bbox = [
                    bbox[1],
                    bbox[0],
                    bbox[3],
                    bbox[2],
                ]

            # Overwrite CRS:84 with EPSG:4326 when specified
            # “CRS:84” refers to WGS 84 geographic longitude and latitude expressed in decimal degrees
            elif crs == CRS.from_user_input("CRS:84"):
                crs = CRS.from_epsg(4326)

        height, width = int(req["height"]), int(req["width"])

        ###########################################################
        # STAC Query parameter provided by the render extension and QueryParameters
        ###########################################################
        query_params = copy(layer.get("render")) or {}

        layer_time = layer.get("time")
        req_time = req.get("time")
        if layer_time and "time" not in req:
            raise HTTPException(
                status_code=400,
                detail=f"Missing 'TIME' parameters for layer {layer['id']}",
            )

        if layer_time and req_time not in layer_time:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid 'TIME' parameter: {req_time}. Not available.",
            )

        if req_time:
            start_datetime = python_datetime.datetime.strptime(
                req_time,
                "%Y-%m-%d",
            ).replace(tzinfo=python_datetime.timezone.utc)
            end_datetime = (
                start_datetime
                + python_datetime.timedelta(days=1)
                - python_datetime.timedelta(
                    milliseconds=1
                )  # prevent inclusion of following day
            )

            query_params["datetime"] = (
                f"{start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            )

        if "color_formula" in req:
            query_params["color_formula"] = req["color_formula"]

        if "expression" in req:
            query_params["expression"] = req["expression"]

        search_query = get_dependency_params(
            dependency=self.search_dependency,
            query_params=query_params,
        )
        search_query["collections"] = [layer["collection"]]

        asset_accessor = get_dependency_params(
            dependency=self.assets_accessor_dependency,
            query_params=query_params,
        )
        layer_params = get_dependency_params(
            dependency=self.layer_dependency,
            query_params=query_params,
        )
        reader_params = get_dependency_params(
            dependency=self.reader_dependency,
            query_params=query_params,
        )
        dataset_params = get_dependency_params(
            dependency=self.dataset_dependency,
            query_params=query_params,
        )
        rendering = get_dependency_params(
            dependency=self.render_dependency,
            query_params=query_params,
        )

        with self.backend(
            search_query,
            reader=self.dataset_reader,
            reader_options={**reader_params.as_dict()},
            api_params=api_params,
        ) as src_dst:
            image, _ = src_dst.part(
                bbox,
                bounds_crs=crs,
                # STAC Query Params
                search_options=asset_accessor.as_dict(),
                pixel_selection=OverlayMethod(),
                threads=MOSAIC_THREADS,
                height=height,
                width=width,
                **layer_params.as_dict(),
                **dataset_params.as_dict(),
            )

        if post_process := get_dependency_params(
            dependency=self.process_dependency,
            query_params=query_params,
        ):
            image = post_process(image)

        if rendering.rescale:
            image.rescale(rendering.rescale)

        if rendering.color_formula:
            image.apply_color_formula(rendering.color_formula)

        return image

    def register_routes(self):  # noqa: C901
        """Register endpoints."""

        # WMTS - KPV Implementation
        @self.router.get(
            "/wmts",
            response_class=Response,
            responses={
                200: {
                    "description": "Web Map Tile Server responses",
                    "content": {
                        "application/xml": {},
                        "application/geo+json": {
                            "schema": FeatureInfo.model_json_schema()
                        },
                        "image/png": {},
                        "image/jpeg": {},
                        "image/jpg": {},
                        "image/webp": {},
                        "image/jp2": {},
                        "image/tiff; application=geotiff": {},
                    },
                },
            },
            openapi_extra={
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "title": "Operation name",
                            "type": "string",
                            "enum": ["GetCapabilities", "GetTile", "GetFeatureInfo"],
                        },
                        "name": "Request",
                        "in": "query",
                    },
                    {
                        "required": True,
                        "schema": {
                            "title": "Service type identifier",
                            "type": "string",
                            "enum": ["wmts"],
                        },
                        "name": "Service",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Standard and schema version",
                            "type": "string",
                            "enum": self.supported_wmts_version,
                        },
                        "name": "Version",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {"title": "Layer identifier"},
                        "name": "Layer",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Output image format",
                            "type": "string",
                            "enum": self.supported_format,
                        },
                        "name": "Format",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {"title": "Style identifier."},
                        "name": "Style",
                        "in": "query",
                    },
                    ################
                    # GetTile
                    {
                        "required": False,
                        "schema": {
                            "title": "TileMatrixSet identifier.",
                            "type": "str",
                            "enum": self.supported_tms.list(),
                        },
                        "name": "TileMatrixSet",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "TileMatrix identifier",
                            "type": "integer",
                        },
                        "name": "TileMatrix",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Row index of tile matrix",
                            "type": "integer",
                        },
                        "name": "TileRow",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Column index of tile matrix",
                            "type": "integer",
                        },
                        "name": "TileCol",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Color Formula",
                            "description": "rio-color formula (info: https://github.com/mapbox/rio-color)",
                            "type": "string",
                        },
                        "name": "color_formula",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Colormap name",
                            "description": "JSON encoded custom Colormap",
                            "type": "string",
                        },
                        "name": "colormap",
                        "in": "query",
                    },
                    ################
                    # GetFeatureInfo
                    # InfoFormat
                    {
                        "required": False,
                        "schema": {
                            "title": "Column index of a pixel in the tile",
                            "type": "integer",
                        },
                        "name": "I",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Row index of a pixel in the tile",
                            "type": "integer",
                        },
                        "name": "J",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Output format of the retrieved information",
                            "type": "str",
                            "enum": ["application/geo+json"],
                        },
                        "name": "InfoFormat",
                        "in": "query",
                    },
                    # TIME dimension
                    {
                        "required": False,
                        "schema": {
                            "title": "Time value of layer desired.",
                            "type": "string",
                        },
                        "name": "Time",
                        "in": "query",
                    },
                ]
            },
        )
        def web_map_tile_service(  # noqa: C901
            request: Request,
            backend_params=Depends(self.backend_dependency),
        ):
            """OGC WMTS Service (KVP encoding)"""
            req = {k.lower(): v for k, v in request.query_params.items()}

            # Service is mandatory
            service = req.get("service")
            if service is None:
                raise HTTPException(
                    status_code=400, detail="Missing WMTS 'SERVICE' parameter."
                )

            if not service.lower() == "wmts":
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid 'SERVICE' parameter: {service}. Only 'wmts' is accepted",
                )

            # Version is mandatory in the specification but we default to 1.0.0
            version = req.get("version", "1.0.0")
            if version is None:
                raise HTTPException(
                    status_code=400, detail="Missing WMTS 'VERSION' parameter."
                )

            if version not in self.supported_wmts_version:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid 'VERSION' parameter: {version}. Allowed versions include: {self.supported_version}",
                )

            # Request is mandatory
            request_type = req.get("request")
            if not request_type:
                raise HTTPException(
                    status_code=400, detail="Missing WMTS 'REQUEST' parameter."
                )

            layers = get_layer_from_collections(
                backend_params.api_params,
                supported_tms=self.supported_tms,
            )

            ###################################################################
            # GetCapabilities request
            if request_type.lower() == "getcapabilities":
                return self.templates.TemplateResponse(
                    request,
                    name=f"wmts-getcapabilities_{version}.xml",
                    context={
                        "request": request,
                        "layers": [layer for _, layer in layers.items()],
                        "service_url": self.url_for(request, "web_map_tile_service"),
                        "tilematrixsets": [
                            self.supported_tms.get(tms)
                            for tms in self.supported_tms.list()
                        ],
                        "media_types": MediaType,
                    },
                    media_type="application/xml",
                )

            ###################################################################
            # GetTile Request
            elif request_type.lower() == "gettile":
                # List of required parameters (styles and crs are excluded)
                req_keys = {
                    "service",
                    "request",
                    "version",
                    "layer",
                    "style",
                    "format",
                    "tilematrixset",
                    "tilematrix",
                    "tilerow",
                    "tilecol",
                }

                intrs = set(req.keys()).intersection(req_keys)
                missing_keys = req_keys.difference(intrs)
                if len(missing_keys) > 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing '{request_type}' parameters: {missing_keys}",
                    )

                if req["format"] not in self.supported_format:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'FORMAT' parameter: {req['format']}. Should be one of {self.supported_format}.",
                    )

                output_format = ImageType(MediaType(req["format"]).name)

                if req["layer"] not in layers:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'LAYER' parameter: {req['layer']}. Should be one of {list(layers)}.",
                    )

                layer = layers[req["layer"]]

                style = layer.get("style", "default").lower()
                req_style = req.get("style") or "default"
                if req_style != style:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid STYLE parameters {req_style} for layer {layer['id']}",
                    )

                image = self.get_tile(
                    req,
                    layer,
                    api_params=backend_params.api_params,
                )

                colormap = get_dependency_params(
                    dependency=self.colormap_dependency,
                    query_params={"colormap": req["colormap"]}
                    if "colormap" in req
                    else layer.get("render") or {},
                )

                content, media_type = render_image(
                    image,
                    output_format=output_format,
                    colormap=colormap,
                    add_mask=True,
                )

                headers: Dict[str, str] = {}
                if image.bounds is not None:
                    headers["Content-Bbox"] = ",".join(map(str, image.bounds))
                if uri := CRS_to_uri(image.crs):
                    headers["Content-Crs"] = f"<{uri}>"

                if (
                    OptionalHeader.server_timing in self.optional_headers
                    and image.metadata.get("timings")
                ):
                    headers["Server-Timing"] = ", ".join(
                        [
                            f"{name};dur={time}"
                            for (name, time) in image.metadata["timings"]
                        ]
                    )

                return Response(content, media_type=media_type)

            ###################################################################
            # GetFeatureInfo Request
            elif request_type.lower() == "getfeatureinfo":
                req_keys = {
                    "service",
                    "request",
                    "version",
                    "layer",
                    "style",
                    # "format",
                    "tilematrixset",
                    "tilematrix",
                    "tilerow",
                    "tilecol",
                    "i",
                    "j",
                    "infoformat",
                }
                intrs = set(req.keys()).intersection(req_keys)
                missing_keys = req_keys.difference(intrs)
                if len(missing_keys) > 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing '{request_type}' parameters: {missing_keys}",
                    )

                if req["infoformat"] != "application/geo+json":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'InfoFormat' parameter: {req['infoformat']}. Should be 'application/geo+json'.",
                    )

                if req["layer"] not in layers:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'LAYER' parameter: {req['layer']}. Should be one of {list(layers)}.",
                    )

                layer = layers[req["layer"]]

                style = layer.get("style", "default").lower()
                req_style = req.get("style") or "default"
                if req_style != style:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid STYLE parameters {req_style} for layer {layer['id']}",
                    )

                image = self.get_tile(
                    req,
                    layer,
                    api_params=backend_params.api_params,
                )

                colormap = get_dependency_params(
                    dependency=self.colormap_dependency,
                    query_params=layer.get("render") or {},
                )
                if colormap:
                    image = image.apply_colormap(colormap)

                i = int(req["i"])
                j = int(req["j"])

                ys, xs = rowcol_to_coords(image.transform, [j], [i])
                xs_wgs84, ys_wgs84 = transform_points(image.crs, "epsg:4326", xs, ys)

                geojson = {
                    "type": "Feature",
                    "id": layer["id"],
                    "geometry": {
                        "type": "Point",
                        "coordinates": (xs_wgs84[0], ys_wgs84[0]),
                    },
                    "properties": {
                        "values": image.data[:, j, i].tolist(),
                        "I": i,
                        "J": j,
                        "style": req_style,
                        "dimension": {"time": req.get("time")},
                        "tileMatrixSet": req["tilematrixset"],
                        "tileMatrix": req["tilematrix"],
                        "tileRow": req["tilerow"],
                        "tileCol": req["tilecol"],
                    },
                }
                return GeoJSONResponse(geojson)

            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid 'REQUEST' parameter: {request_type}. Should be one of ['GetCapabilities', 'GetTile', 'GetFeatureInfo'].",
                )

        @self.router.get(
            "/layers/{LAYER}/{STYLE}/{TIME}/{TileMatrixSet}/{TileMatrix}/{TileCol}/{TileRow}.{FORMAT}",
            **img_endpoint_params,
        )
        def WMTS_getTile(
            request: Request,
            collectionId: Annotated[
                str,
                Path(
                    description="Layer Identifier (Collection ID)",
                    alias="LAYER",
                ),
            ],
            styleId: Annotated[
                Literal["default"],
                Path(
                    description="Style Identifier",
                    alias="STYLE",
                ),
            ],
            timeId: Annotated[
                str,
                Path(
                    description="Time Dimension Identifier",
                    alias="TIME",
                ),
            ],
            tileMatrixSetId: Annotated[  # type: ignore
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported",
                    alias="TileMatrixSet",
                ),
            ],
            z: Annotated[
                int,
                Path(
                    description="Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile.",
                    alias="TileMatrix",
                ),
            ],
            x: Annotated[
                int,
                Path(
                    description="Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 for the selected TileMatrix.",
                    alias="TileCol",
                ),
            ],
            y: Annotated[
                int,
                Path(
                    description="Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 for the selected TileMatrix.",
                    alias="TileRow",
                ),
            ],
            format: Annotated[
                ImageType,
                Path(
                    description="Output Image format",
                    alias="FORMAT",
                ),
            ],
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            assets_accessor_params=Depends(self.assets_accessor_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            env=Depends(self.environment_dependency),
        ):
            """OGC WMTS GetTile (REST encoding) used in WMTS TileURLTemplate."""
            search_query: Search = {"collections": [collectionId], "datetime": timeId}

            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                with self.backend(
                    search_query,
                    tms=tms,
                    reader=self.dataset_reader,
                    reader_options={**reader_params.as_dict()},
                    **backend_params.as_dict(),
                ) as src_dst:
                    if MOSAIC_STRICT_ZOOM and (
                        z < src_dst.minzoom or z > src_dst.maxzoom
                    ):
                        raise HTTPException(
                            400,
                            f"Invalid ZOOM level {z}. Should be between {src_dst.minzoom} and {src_dst.maxzoom}",
                        )

                    image, assets = src_dst.tile(
                        x,
                        y,
                        z,
                        tilesize=256,
                        search_options=assets_accessor_params.as_dict(),
                        pixel_selection=pixel_selection,
                        threads=MOSAIC_THREADS,
                        **tile_params.as_dict(),
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                    )

            if post_process:
                image = post_process(image)

            content, media_type = render_image(
                image,
                output_format=format,
                colormap=colormap,
                **render_params.as_dict(),
            )

            headers: Dict[str, str] = {}
            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(assets)

            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            if (
                OptionalHeader.server_timing in self.optional_headers
                and image.metadata.get("timings")
            ):
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in image.metadata["timings"]]
                )

            return Response(content, media_type=media_type)

        @self.router.get(
            "/wms",
            response_class=Response,
            responses={
                200: {
                    "description": "Web Map Server responses",
                    "content": {
                        "application/xml": {},
                        "image/png": {},
                        "image/jpeg": {},
                        "image/jpg": {},
                        "image/webp": {},
                        "image/jp2": {},
                        "image/tiff; application=geotiff": {},
                    },
                },
            },
            openapi_extra={
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "title": "Request name",
                            "type": "string",
                            "enum": ["GetCapabilities", "GetMap", "GetFeatureInfo"],
                        },
                        "name": "REQUEST",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "WMS Service type",
                            "type": "string",
                            "enum": ["wms"],
                        },
                        "name": "SERVICE",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "WMS Request version",
                            "type": "string",
                            "enum": [
                                "1.1.0",
                                "1.1.1",
                                "1.3.0",
                            ],
                        },
                        "name": "VERSION",
                        "in": "query",
                    },
                    {
                        "required": True,
                        "schema": {
                            "title": "Comma-separated list of one or more map layers."
                        },
                        "name": "LAYERS",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Output format of service metadata/map",
                            "type": "string",
                            "enum": [
                                "text/html",
                                "application/xml",
                                "image/png",
                                "image/jpeg",
                                "image/jpg",
                                "image/webp",
                                "image/jp2",
                                "image/tiff; application=geotiff",
                            ],
                        },
                        "name": "FORMAT",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Sequence number or string for cache control"
                        },
                        "name": "UPDATESEQUENCE",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Coordinate reference system.",
                            "type": "string",
                        },
                        "name": "CRS",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Bounding box corners (lower left, upper right) in CRS units.",
                            "type": "string",
                        },
                        "name": "BBOX",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Width in pixels of map picture.",
                            "type": "integer",
                        },
                        "name": "WIDTH",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Height in pixels of map picture.",
                            "type": "integer",
                        },
                        "name": "HEIGHT",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "I Coordinate in pixels of feature in Map CS.",
                            "type": "integer",
                        },
                        "name": "i",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "J Coordinate in pixels of feature in Map CS.",
                            "type": "integer",
                        },
                        "name": "j",
                        "in": "query",
                    },
                    # Non-Used
                    {
                        "required": False,
                        "schema": {
                            "title": "Comma-separated list of one rendering style per requested layer."
                        },
                        "name": "STYLES",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "Background transparency of map (default=FALSE).",
                            "type": "boolean",
                            "default": False,
                        },
                        "name": "TRANSPARENT",
                        "in": "query",
                    },
                    # {
                    #     "required": False,
                    #     "schema": {
                    #         "title": "Hexadecimal red-green-blue colour value for the background color (default=FFFFFF).",
                    #         "type": "string",
                    #         "default": "FFFFFF",
                    #     },
                    #     "name": "BGCOLOR",
                    #     "in": "query",
                    # },
                    {
                        "required": False,
                        "schema": {
                            "title": "The format in which exceptions are to be reported by the WMS (default=JSON).",
                            "type": "string",
                            "enum": ["JSON"],
                        },
                        "name": "EXCEPTIONS",
                        "in": "query",
                    },
                    # TIME dimension
                    {
                        "required": False,
                        "schema": {
                            "title": "Time value of layer desired.",
                            "type": "string",
                        },
                        "name": "Time",
                        "in": "query",
                    },
                    # {
                    #     "required": False,
                    #     "schema": {
                    #         "title": "Elevation of layer desired.",
                    #         "type": "string",
                    #     },
                    #     "name": "ELEVATION",
                    #     "in": "query",
                    # },
                ]
            },
        )
        def web_map_service(  # noqa: C901
            request: Request,
            backend_params=Depends(self.backend_dependency),
        ):
            """OGC WMS endpoint.

            Capabilities:
                - GetCapability generates a WMS XML definition.
                - GetMap returns an Image

            """
            req = {k.lower(): v for k, v in request.query_params.items()}

            # Required parameters:
            # - SERVICE=WMS
            # - REQUEST
            # Optional parameters: VERSION

            # Service is mandatory
            service = req.get("service")
            if service is None:
                raise HTTPException(
                    status_code=400, detail="Missing WMS 'SERVICE' parameter."
                )

            if not req["service"].lower() == "wms":
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid 'SERVICE' parameter: {req['service']}. Only 'wms' is accepted",
                )

            # Version is mandatory in the specification but we default to 1.3.0
            version = req.get("version", "1.3.0")
            if version not in self.supported_wms_version:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid 'VERSION' parameter: {version}. Allowed versions include: {self.supported_wms_version}",
                )

            # Request is mandatory
            request_type = req.get("request")
            if not request_type:
                raise HTTPException(
                    status_code=400, detail="Missing WMS 'REQUEST' parameter."
                )

            # inlayers = req.get("layers")
            # if inlayers is None:
            #     raise HTTPException(
            #         status_code=400, detail="Missing WMS 'LAYERS' parameter."
            #     )
            #
            # layers = list(inlayers.split(","))
            # if not layers or not inlayers:
            #     raise HTTPException(
            #         status_code=400,
            #         detail=f"Invalid 'LAYERS' parameter: {inlayers}.",
            #     )

            layers = get_layer_from_collections(backend_params.api_params)

            # GetCapabilities: Return a WMS XML
            if request_type.lower() == "getcapabilities":
                wms_url = self.url_for(request, "wms")

                qs_key_to_remove = [
                    "service",
                    "request",
                    "layers",
                    "version",
                    "format",
                    "updatesequence",
                ]
                qs = [
                    (key, value)
                    for (key, value) in request.query_params._list
                    if key.lower() not in qs_key_to_remove
                ]
                if qs:
                    wms_url += f"?{urlencode(qs)}"

                # Grab information from each layer provided
                layers_dict: Dict[str, Any] = {}
                for lay in layers:
                    layers_dict[lay] = {}
                    layers_dict[lay]["srs"] = "EPSG:4326"
                    layers_dict[lay]["bounds"] = layers[lay]["bbox"]  # type: ignore
                    layers_dict[lay]["bounds_wgs84"] = layers[lay]["bbox"]  # type: ignore

                # Build information for the whole service
                minx, miny, maxx, maxy = zip(
                    *[layers_dict[lay]["bounds_wgs84"] for lay in layers]
                )

                return self.templates.TemplateResponse(
                    request,
                    name=f"wms_{version}.xml",
                    context={
                        "request": request,
                        "request_url": wms_url,
                        "formats": self.supported_format,
                        "available_epsgs": self.supported_crs,
                        "layers_dict": layers_dict,
                        "service_dict": {
                            "xmin": min(minx),
                            "ymin": min(miny),
                            "xmax": max(maxx),
                            "ymax": max(maxy),
                        },
                    },
                    media_type="application/xml",
                )

            elif request_type.lower() == "getmap":
                # Required parameters:
                # - LAYERS
                # - CRS or SRS
                # - WIDTH
                # - HEIGHT
                # - QUERY_LAYERS
                # - FORMAT
                # Optional parameters:
                # - transparent

                req_keys = {
                    "layers",
                    "bbox",
                    "width",
                    "height",
                    "format",
                }

                if req["layers"] not in layers:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'LAYER' parameter: {req['layer']}. Should be one of {list(layers)}.",
                    )

                layer = layers[req["layers"]]

                image = self.get_map_data(
                    req,
                    req_keys,
                    request_type,
                    layer,
                    api_params=backend_params.api_params,
                    version=version,
                )

                if transparent := req.get("transparent", False):
                    if str(transparent).lower() == "true":
                        transparent = True

                    elif str(transparent).lower() == "false":
                        transparent = False

                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid 'TRANSPARENT' parameter: {transparent}. Should be one of ['FALSE', 'TRUE'].",
                        )

                format = req["format"]
                if format not in self.supported_format:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'FORMAT' parameter: {format}. Should be one of {self.supported_format}.",
                    )
                output_format = ImageType(MediaType(format).name)

                colormap = get_dependency_params(
                    dependency=self.colormap_dependency,
                    query_params={"colormap": req["colormap"]}
                    if "colormap" in req
                    else layer.get("render") or {},
                )

                content, media_type = render_image(
                    image,
                    output_format=output_format,
                    colormap=colormap,
                    add_mask=True,
                )

                headers: Dict[str, str] = {}
                if image.bounds is not None:
                    headers["Content-Bbox"] = ",".join(map(str, image.bounds))
                if uri := CRS_to_uri(image.crs):
                    headers["Content-Crs"] = f"<{uri}>"

                if (
                    OptionalHeader.server_timing in self.optional_headers
                    and image.metadata.get("timings")
                ):
                    headers["Server-Timing"] = ", ".join(
                        [
                            f"{name};dur={time}"
                            for (name, time) in image.metadata["timings"]
                        ]
                    )

                return Response(content, media_type=media_type)

            elif request_type.lower() == "getfeatureinfo":
                # Required parameters:
                # - LAYERS
                # - CRS or SRS
                # - BBOX
                # - WIDTH
                # - HEIGHT
                # - QUERY_LAYERS
                # - I (Pixel column)
                # - J (Pixel row)
                # Optional parameters: INFO_FORMAT, FEATURE_COUNT, ...

                req_keys = {
                    "version",
                    "request",
                    "layers",
                    "width",
                    "height",
                    "query_layers",
                    "i",
                    "j",
                }

                if req["layers"] not in layers:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid 'LAYER' parameter: {req['layer']}. Should be one of {list(layers)}.",
                    )

                layer = layers[req["layers"]]

                image = self.get_map_data(
                    req,
                    req_keys,
                    request_type,
                    layer,
                    api_params=backend_params.api_params,
                    version=version,
                )
                i = int(req["i"])
                j = int(req["j"])

                html_content = ""
                bands_info = []
                for band in range(image.count):
                    pixel_value = image.data[band, j, i]
                    bands_info.append(pixel_value)

                html_content = ",".join([str(band_info) for band_info in bands_info])
                return Response(html_content, 200)

            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid 'REQUEST' parameter: {request_type}. Should be one of ['GetCapabilities', 'GetMap'].",
                )
