"""Custom MosaicTiler Factory for TiTiler-STACAPI Mosaic Backend."""

import datetime as python_datetime
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Type
from urllib.parse import urlencode

import jinja2
import rasterio
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from cogeo_mosaic.backends import BaseBackend
from fastapi import Depends, HTTPException, Path, Query
from fastapi.dependencies.utils import get_dependant, request_params_to_args
from morecantile import tms as morecantile_tms
from morecantile.defaults import TileMatrixSets
from pydantic import conint
from pystac_client import Client
from pystac_client.stac_api_io import StacApiIO
from rasterio.transform import xy as rowcol_to_coords
from rasterio.warp import transform as transform_points
from rio_tiler.constants import MAX_THREADS
from rio_tiler.models import ImageData
from rio_tiler.mosaic.methods.base import MosaicMethodBase
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import compile_path, replace_params
from starlette.templating import Jinja2Templates
from typing_extensions import Annotated
from urllib3 import Retry

from titiler.core.dependencies import (
    AssetsBidxExprParams,
    ColorFormulaParams,
    DefaultDependency,
    TileParams,
)
from titiler.core.factory import BaseTilerFactory, img_endpoint_params
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType, MediaType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse, XMLResponse
from titiler.core.utils import render_image
from titiler.mosaic.factory import PixelSelectionParams
from titiler.stacapi.backend import STACAPIBackend
from titiler.stacapi.dependencies import APIParams, STACApiParams, STACSearchParams
from titiler.stacapi.models import FeatureInfo, LayerDict
from titiler.stacapi.settings import CacheSettings, RetrySettings
from titiler.stacapi.utils import _tms_limits

cache_config = CacheSettings()
retry_config = RetrySettings()

MOSAIC_THREADS = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))
MOSAIC_STRICT_ZOOM = str(os.getenv("MOSAIC_STRICT_ZOOM", False)).lower() in [
    "true",
    "yes",
]

jinja2_env = jinja2.Environment(
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

    return


@dataclass
class MosaicTilerFactory(BaseTilerFactory):
    """Custom MosaicTiler for STACAPI Mosaic Backend."""

    path_dependency: Callable[..., APIParams] = STACApiParams

    search_dependency: Callable[..., Dict] = STACSearchParams

    # In this factory, `reader` should be a Mosaic Backend
    # https://developmentseed.org/cogeo-mosaic/advanced/backends/
    reader: Type[BaseBackend] = STACAPIBackend

    # Because the endpoints should work with STAC Items,
    # the `layer_dependency` define which query parameters are mandatory/optional to `display` images
    # Defaults to `titiler.core.dependencies.AssetsBidxExprParams`, `assets=` or `expression=` is required
    layer_dependency: Type[DefaultDependency] = AssetsBidxExprParams

    # The `tile_dependency` define options like `buffer` or `padding`
    # used in Tile/Tilejson/WMTS Dependencies
    tile_dependency: Type[DefaultDependency] = TileParams

    pixel_selection_dependency: Callable[..., MosaicMethodBase] = PixelSelectionParams

    backend_dependency: Type[DefaultDependency] = DefaultDependency

    add_viewer: bool = False

    templates: Jinja2Templates = DEFAULT_TEMPLATES

    def get_base_url(self, request: Request) -> str:
        """return endpoints base url."""
        base_url = str(request.base_url).rstrip("/")
        if self.router_prefix:
            prefix = self.router_prefix.lstrip("/")
            # If we have prefix with custom path param we check and replace them with
            # the path params provided
            if "{" in prefix:
                _, path_format, param_convertors = compile_path(prefix)
                prefix, _ = replace_params(
                    path_format, param_convertors, request.path_params.copy()
                )
            base_url += prefix

        return base_url

    def register_routes(self) -> None:
        """register endpoints."""

        self.register_tiles()
        self.register_tilejson()
        self.register_wmts()
        if self.add_viewer:
            self.register_map()

    def register_tiles(self) -> None:
        """register tiles routes."""

        @self.router.get("/tiles/{tileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        def tile(
            request: Request,
            tileMatrixSetId: Annotated[  # type: ignore
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported"
                ),
            ],
            z: Annotated[
                int,
                Path(
                    description="Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile.",
                ),
            ],
            x: Annotated[
                int,
                Path(
                    description="Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 for the selected TileMatrix.",
                ),
            ],
            y: Annotated[
                int,
                Path(
                    description="Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 for the selected TileMatrix.",
                ),
            ],
            api_params=Depends(self.path_dependency),
            search_query=Depends(self.search_dependency),
            scale: Annotated[  # type: ignore
                Optional[conint(gt=0, le=4)],
                "Tile size scale. 1=256x256, 2=512x512...",
            ] = None,
            format: Annotated[
                Optional[ImageType],
                "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
            ] = None,
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(ColorFormulaParams),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Create map tile."""
            scale = scale or 1

            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                with self.reader(
                    url=api_params["api_url"],
                    headers=api_params.get("headers", {}),
                    tms=tms,
                    reader_options={**reader_params},
                    **backend_params,
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
                        search_query=search_query,
                        tilesize=scale * 256,
                        pixel_selection=pixel_selection,
                        threads=MOSAIC_THREADS,
                        **tile_params,
                        **layer_params,
                        **dataset_params,
                    )

            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            content, media_type = render_image(
                image,
                output_format=format,
                colormap=colormap,
                **render_params,
            )

            headers: Dict[str, str] = {}
            if OptionalHeader.x_assets in self.optional_headers:
                ids = [x["id"] for x in assets]
                headers["X-Assets"] = ",".join(ids)

            if (
                OptionalHeader.server_timing in self.optional_headers
                and image.metadata.get("timings")
            ):
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in image.metadata["timings"]]
                )

            return Response(content, media_type=media_type, headers=headers)

    def register_tilejson(self) -> None:
        """register tiles routes."""

        @self.router.get(
            "/{tileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        def tilejson(
            request: Request,
            tileMatrixSetId: Annotated[  # type: ignore
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported"
                ),
            ],
            search_query=Depends(self.search_dependency),
            tile_format: Annotated[
                Optional[ImageType],
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            tile_scale: Annotated[
                Optional[int],
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = None,
            minzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default maxzoom."),
            ] = None,
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(ColorFormulaParams),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
        ):
            """Return TileJSON document."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "tileMatrixSetId": tileMatrixSetId,
            }

            if tile_scale:
                route_params["scale"] = tile_scale

            if tile_format:
                route_params["format"] = tile_format.value

            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            tms = self.supported_tms.get(tileMatrixSetId)
            minzoom = minzoom if minzoom is not None else tms.minzoom
            maxzoom = maxzoom if maxzoom is not None else tms.maxzoom
            bounds = search_query.get("bbox") or tms.bbox

            return {
                "bounds": bounds,
                "minzoom": minzoom,
                "maxzoom": maxzoom,
                "name": "STACAPI",
                "tiles": [tiles_url],
            }

    def register_map(self):  # noqa: C901
        """Register /map endpoint."""

        @self.router.get("/{tileMatrixSetId}/map", response_class=HTMLResponse)
        def map_viewer(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported"
                ),
            ],
            search_query=Depends(self.search_dependency),
            tile_format: Annotated[
                Optional[ImageType],
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            tile_scale: Annotated[
                Optional[int],
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = None,
            minzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default maxzoom."),
            ] = None,
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(ColorFormulaParams),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Return a simple map viewer."""
            tilejson_url = self.url_for(
                request,
                "tilejson",
                tileMatrixSetId=tileMatrixSetId,
            )
            if request.query_params._list:
                tilejson_url += f"?{urlencode(request.query_params._list)}"

            tms = self.supported_tms.get(tileMatrixSetId)

            return self.templates.TemplateResponse(
                name="map.html",
                context={
                    "request": request,
                    "tilejson_endpoint": tilejson_url,
                    "tms": tms,
                    "resolutions": [matrix.cellSize for matrix in tms],
                    "template": {
                        "api_root": str(request.base_url).rstrip("/"),
                        "params": request.query_params,
                        "title": "Map",
                    },
                },
                media_type="text/html",
            )

    def register_wmts(self):  # noqa: C901
        """Add wmts endpoint."""

        @self.router.get(
            "/{tileMatrixSetId}/WMTSCapabilities.xml",
            response_class=XMLResponse,
        )
        def wmts(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported"
                ),
            ],
            search_query=Depends(self.search_dependency),
            tile_format: Annotated[
                ImageType,
                Query(description="Output image type. Default is png."),
            ] = ImageType.png,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            minzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default maxzoom."),
            ] = None,
        ):
            """OGC WMTS endpoint."""
            route_params = {
                "z": "{TileMatrix}",
                "x": "{TileCol}",
                "y": "{TileRow}",
                "scale": tile_scale,
                "format": tile_format.value,
                "tileMatrixSetId": tileMatrixSetId,
            }

            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
                "service",
                "request",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            tms = self.supported_tms.get(tileMatrixSetId)
            minzoom = minzoom if minzoom is not None else tms.minzoom
            maxzoom = maxzoom if maxzoom is not None else tms.maxzoom
            bounds = search_query.get("bbox") or tms.bbox

            tileMatrix = []
            for zoom in range(minzoom, maxzoom + 1):  # type: ignore
                matrix = tms.matrix(zoom)
                tm = f"""
                        <TileMatrix>
                            <ows:Identifier>{matrix.id}</ows:Identifier>
                            <ScaleDenominator>{matrix.scaleDenominator}</ScaleDenominator>
                            <TopLeftCorner>{matrix.pointOfOrigin[0]} {matrix.pointOfOrigin[1]}</TopLeftCorner>
                            <TileWidth>{matrix.tileWidth}</TileWidth>
                            <TileHeight>{matrix.tileHeight}</TileHeight>
                            <MatrixWidth>{matrix.matrixWidth}</MatrixWidth>
                            <MatrixHeight>{matrix.matrixHeight}</MatrixHeight>
                        </TileMatrix>"""
                tileMatrix.append(tm)

            return self.templates.TemplateResponse(
                "wmts.xml",
                {
                    "request": request,
                    "title": "STAC API",
                    "bounds": bounds,
                    "tileMatrix": tileMatrix,
                    "tms": tms,
                    "media_type": tile_format.mediatype,
                },
                media_type="application/xml",
            )


class WMTSMediaType(str, Enum):
    """Responses Media types for WMTS"""

    tif = "image/tiff; application=geotiff"
    jp2 = "image/jp2"
    png = "image/png"
    jpeg = "image/jpeg"
    jpg = "image/jpg"
    webp = "image/webp"


@cached(  # type: ignore
    TTLCache(maxsize=cache_config.maxsize, ttl=cache_config.ttl),
    key=lambda url, headers, supported_tms: hashkey(url, json.dumps(headers)),
)
def get_layer_from_collections(  # noqa: C901
    url: str,
    headers: Optional[Dict] = None,
    supported_tms: Optional[TileMatrixSets] = None,
) -> Dict[str, LayerDict]:
    """Get Layers from STAC Collections."""
    supported_tms = supported_tms or morecantile_tms

    stac_api_io = StacApiIO(
        max_retries=Retry(
            total=retry_config.retry,
            backoff_factor=retry_config.retry_factor,
        ),
        headers=headers,
    )
    catalog = Client.open(url, stac_io=stac_api_io)

    layers: Dict[str, LayerDict] = {}
    for collection in catalog.get_collections():
        spatial_extent = collection.extent.spatial
        temporal_extent = collection.extent.temporal

        if "renders" in collection.extra_fields:
            for name, render in collection.extra_fields["renders"].items():

                tilematrixsets = render.pop("tilematrixsets", None)
                output_format = render.pop("format", None)

                _ = render.pop("minmax_zoom", None)  # Not Used
                _ = render.pop("title", None)  # Not Used

                # see https://github.com/developmentseed/eoAPI-vito/issues/9#issuecomment-2034025021
                render_title = f"{collection.id}_{name}"
                layer = {
                    "id": render_title,
                    "collection": collection.id,
                    "bbox": [-180, -90, 180, 90],
                    "style": "default",
                    "render": render,
                }
                if output_format:
                    layer["format"] = output_format

                if spatial_extent:
                    layer["bbox"] = spatial_extent.bboxes[0]

                # NB. The WMTS spec is contradictory re. the multiplicity
                # relationships between Layer and TileMatrixSetLink, and
                # TileMatrixSetLink and tileMatrixSet (URI).
                # WMTS only support 1 set of limits for a TileMatrixSet
                if tilematrixsets:
                    if len(tilematrixsets) == 1:
                        layer["tilematrixsets"] = {
                            tms_id: _tms_limits(
                                supported_tms.get(tms_id), layer["bbox"], zooms=zooms
                            )
                            for tms_id, zooms in tilematrixsets.items()
                        }
                    else:
                        layer["tilematrixsets"] = {
                            tms_id: None for tms_id, _ in tilematrixsets.items()
                        }

                else:
                    tilematrixsets = supported_tms.list()
                    if len(tilematrixsets) == 1:
                        layer["tilematrixsets"] = {
                            tms_id: _tms_limits(
                                supported_tms.get(tms_id), layer["bbox"]
                            )
                            for tms_id in tilematrixsets
                        }
                    else:
                        layer["tilematrixsets"] = {
                            tms_id: None for tms_id in tilematrixsets
                        }

                # TODO: handle multiple intervals
                # Check datacube extension
                # https://github.com/stac-extensions/datacube?tab=readme-ov-file#temporal-dimension-object
                if intervals := temporal_extent.intervals:
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

                layers[render_title] = LayerDict(
                    id=layer["id"],
                    collection=layer["collection"],
                    bbox=layer["bbox"],
                    format=layer.get("format"),
                    style=layer["style"],
                    render=layer.get("render", {}),
                    tilematrixsets=layer["tilematrixsets"],
                    time=layer.get("time"),
                    query_string=layer["query_string"],
                )

    return layers


@dataclass
class OGCWMTSFactory(BaseTilerFactory):
    """Create /wmts endpoint"""

    path_dependency: Callable[..., APIParams] = STACApiParams

    # In this factory, `reader` should be a Mosaic Backend
    # https://developmentseed.org/cogeo-mosaic/advanced/backends/
    reader: Type[BaseBackend] = STACAPIBackend

    # Because the endpoints should work with STAC Items,
    # the `layer_dependency` define which query parameters are mandatory/optional to `display` images
    # Defaults to `titiler.core.dependencies.AssetsBidxExprParams`, `assets=` or `expression=` is required
    layer_dependency: Type[DefaultDependency] = AssetsBidxExprParams

    # The `tile_dependency` define options like `buffer` or `padding`
    # used in Tile/Tilejson/WMTS Dependencies
    tile_dependency: Type[DefaultDependency] = TileParams

    pixel_selection_dependency: Callable[..., MosaicMethodBase] = PixelSelectionParams

    backend_dependency: Type[DefaultDependency] = DefaultDependency

    supported_format: List[str] = field(
        default_factory=lambda: [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
            "image/jp2",
            "image/tiff; application=geotiff",
        ]
    )

    supported_version: List[str] = field(default_factory=lambda: ["1.0.0"])

    templates: Jinja2Templates = DEFAULT_TEMPLATES

    def get_tile(  # noqa: C901
        self,
        req: Dict,
        layer: LayerDict,
        stac_url: str,
        headers: Optional[Dict] = None,
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

        tms = self.supported_tms.get(tms_id)
        with self.reader(
            url=stac_url,
            headers=headers,
            tms=tms,
        ) as src_dst:
            if MOSAIC_STRICT_ZOOM and (z < src_dst.minzoom or z > src_dst.maxzoom):
                raise HTTPException(
                    400,
                    f"Invalid ZOOM level {z}. Should be between {src_dst.minzoom} and {src_dst.maxzoom}",
                )

            ###########################################################
            # STAC Query parameter provided by the the render extension and QueryParameters
            ###########################################################
            search_query: Dict[str, Any] = {
                "collections": [layer["collection"]],
            }

            if req_time:
                start_datetime = python_datetime.datetime.strptime(
                    req_time,
                    "%Y-%m-%d",
                ).replace(tzinfo=python_datetime.timezone.utc)
                end_datetime = start_datetime + python_datetime.timedelta(days=1)

                search_query[
                    "datetime"
                ] = f"{start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}"

            query_params = layer.get("render") or {}
            layer_params = get_dependency_params(
                dependency=self.layer_dependency,
                query_params=query_params,
            )
            tile_params = get_dependency_params(
                dependency=self.tile_dependency,
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

            image, _ = src_dst.tile(
                x,
                y,
                z,
                # STAC Query Params
                search_query=search_query,
                pixel_selection=pixel_selection,
                threads=MOSAIC_THREADS,
                **tile_params,
                **layer_params,
                **dataset_params,
            )

            if post_process := get_dependency_params(
                dependency=self.process_dependency,
                query_params=query_params,
            ):
                image = post_process(image)

            if rescale := get_dependency_params(
                dependency=self.rescale_dependency,
                query_params=query_params,
            ):
                image.rescale(rescale)

            if color_formula := get_dependency_params(
                dependency=self.color_formula_dependency,
                query_params=query_params,
            ):
                image.apply_color_formula(color_formula)

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
                        "application/geo+json": {"schema": FeatureInfo.schema()},
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
                            "enum": self.supported_version,
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
            api_params=Depends(self.path_dependency),
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

            # Version is mandatory is mandatory in the specification but we default to 1.0.0
            version = req.get("version", "1.0.0")
            if version is None:
                raise HTTPException(
                    status_code=400, detail="Missing WMTS 'VERSION' parameter."
                )

            if version not in self.supported_version:
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
                url=api_params["api_url"],
                headers=api_params.get("headers", {}),
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
                        "layers": [layer for k, layer in layers.items()],
                        "service_url": self.url_for(request, "web_map_tile_service"),
                        "tilematrixsets": [
                            self.supported_tms.get(tms)
                            for tms in self.supported_tms.list()
                        ],
                        "media_types": WMTSMediaType,
                    },
                    media_type=MediaType.xml.value,
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

                output_format = ImageType(WMTSMediaType(req["format"]).name)

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
                    stac_url=api_params["api_url"],
                    headers=api_params.get("headers", {}),
                )

                colormap = get_dependency_params(
                    dependency=self.colormap_dependency,
                    query_params=layer.get("render") or {},
                )

                content, media_type = render_image(
                    image,
                    output_format=output_format,
                    colormap=colormap,
                    add_mask=True,
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
                    stac_url=api_params["api_url"],
                    headers=api_params.get("headers", {}),
                )

                colormap = get_dependency_params(
                    dependency=self.colormap_dependency,
                    query_params=layer.get("render") or {},
                )
                if colormap:
                    image = image.apply_colormap(colormap)

                # output_format = ImageType(WMTSMediaType(req["format"]).name)

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
                    description="Layer Identifier",
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
            api_params=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection=Depends(self.pixel_selection_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(ColorFormulaParams),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            backend_params=Depends(self.backend_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
        ):
            """OGC WMTS GetTile (REST encoding)"""
            search_query = {"collections": [collectionId], "datetime": timeId}

            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                with self.reader(
                    url=api_params["api_url"],
                    headers=api_params.get("headers", {}),
                    tms=tms,
                    reader_options={**reader_params},
                    **backend_params,
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
                        search_query=search_query,
                        tilesize=256,
                        pixel_selection=pixel_selection,
                        threads=MOSAIC_THREADS,
                        **tile_params,
                        **layer_params,
                        **dataset_params,
                    )

            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            content, media_type = render_image(
                image,
                output_format=format,
                colormap=colormap,
                **render_params,
            )

            return Response(content, media_type=media_type)
