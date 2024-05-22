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
    # used in Tile/Tilejson Dependencies
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

