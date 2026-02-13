"""titiler-stacapi custom Mosaic Backend and Custom STACReader."""

import json
from threading import Lock
from typing import Any

import attr
import pystac
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from geojson_pydantic import Point, Polygon
from geojson_pydantic.geometries import Geometry
from morecantile import Tile, TileMatrixSet
from pystac_client import Client, ItemSearch
from pystac_client.stac_api_io import StacApiIO
from rasterio.crs import CRS
from rasterio.warp import transform, transform_bounds
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.mosaic.backend import BaseBackend, MosaicInfo
from rio_tiler.types import BBox
from rio_tiler.utils import CRS_to_uri
from urllib3 import Retry

from titiler.stacapi.dependencies import APIParams, Search
from titiler.stacapi.reader import SimpleSTACReader
from titiler.stacapi.settings import CacheSettings, RetrySettings

cache_config = CacheSettings()
retry_config = RetrySettings()

ttl_cache = TTLCache(maxsize=cache_config.maxsize, ttl=cache_config.ttl)  # type: ignore


@attr.s
class STACAPIBackend(BaseBackend):
    """STACAPI Mosaic Backend."""

    # STAC API URL
    input: Search = attr.ib()
    api_params: APIParams = attr.ib()

    # Because we are not using mosaicjson we are not limited to the WebMercator TMS
    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)

    # Use Custom STAC reader (outside init)
    reader: type[SimpleSTACReader] = attr.ib(default=SimpleSTACReader)
    reader_options: dict = attr.ib(factory=dict)

    # default values for bounds
    bounds: BBox = attr.ib(default=(-180, -90, 180, 90))
    crs: CRS = attr.ib(default=WGS84_CRS)

    _backend_name = "STACAPI"

    def __attrs_post_init__(self):
        """Post Init."""
        if bbox := self.input.get("bbox"):
            self.bounds = tuple(bbox)

    @property
    def minzoom(self) -> int:
        """Return minzoom."""
        return self.tms.minzoom

    @property
    def maxzoom(self) -> int:
        """Return maxzoom."""
        return self.tms.maxzoom

    # in STACAPI backend assets are STAC Items as dict
    def asset_name(self, asset: dict) -> str:
        """Get asset name."""
        return f"{asset['collection']}/{asset['id']}"

    def assets_for_tile(self, x: int, y: int, z: int, **kwargs: Any) -> list[dict]:
        """Retrieve assets for tile."""
        bbox = self.tms.bounds(Tile(x, y, z))
        return self.get_assets(Polygon.from_bounds(*bbox), **kwargs)

    def assets_for_point(
        self,
        lng: float,
        lat: float,
        coord_crs: CRS = WGS84_CRS,
        **kwargs: Any,
    ) -> list[dict]:
        """Retrieve assets for point."""
        if coord_crs != WGS84_CRS:
            xs, ys = transform(coord_crs, WGS84_CRS, [lng], [lat])
            lng, lat = xs[0], ys[0]

        return self.get_assets(Point(type="Point", coordinates=(lng, lat)), **kwargs)

    def assets_for_bbox(
        self,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        coord_crs: CRS = WGS84_CRS,
        **kwargs: Any,
    ) -> list[dict]:
        """Retrieve assets for bbox."""
        if coord_crs != WGS84_CRS:
            xmin, ymin, xmax, ymax = transform_bounds(
                coord_crs,
                WGS84_CRS,
                xmin,
                ymin,
                xmax,
                ymax,
            )

        return self.get_assets(Polygon.from_bounds(xmin, ymin, xmax, ymax), **kwargs)

    @cached(  # type: ignore
        ttl_cache,
        key=lambda self, geom, **kwargs: hashkey(
            self.api_params["url"],
            str(geom),
            json.dumps(self.input),
            json.dumps(self.api_params.get("headers", {})),
            **kwargs,
        ),
        lock=Lock(),
    )
    def get_assets(
        self,
        geom: Geometry,
        sortby: list[dict] | None = None,
        limit: int | None = None,
        max_items: int | None = None,
        fields: list[str] | None = None,
    ) -> list[dict]:
        """Find assets."""

        search_query = {
            **self.input,
            "method": "GET" if self.input.get("filter_expr") else "POST",
            "sortby": sortby,
            "limit": limit or 10,
            "max_items": max_items or 100,
        }
        fields = fields or ["assets", "id", "bbox", "collection"]

        stac_api_io = StacApiIO(
            max_retries=Retry(
                total=retry_config.retry,
                backoff_factor=retry_config.retry_factor,
            ),
            headers=self.api_params.get("headers", {}),
        )

        params = {
            **search_query,
            "intersects": geom.model_dump_json(exclude_none=True),
            "fields": fields,
        }
        params.pop("bbox", None)

        results = ItemSearch(
            f"{self.api_params['url']}/search", stac_io=stac_api_io, **params
        )
        return list(results.items_as_dicts())

    @cached(  # type: ignore
        ttl_cache,
        key=lambda self, collection_id: hashkey(
            collection_id,
            self.api_params["url"],
            json.dumps(self.input),
            json.dumps(self.api_params.get("headers", {})),
        ),
        lock=Lock(),
    )
    def _get_collection(self, collection_id) -> pystac.Collection:
        stac_api_io = StacApiIO(
            max_retries=Retry(
                total=retry_config.retry,
                backoff_factor=retry_config.retry_factor,
            ),
            headers=self.api_params.get("headers", {}),
        )
        client = Client.open(f"{self.api_params['url']}", stac_io=stac_api_io)
        return client.get_collection(collection_id)

    def get_geographic_bounds(self, crs: CRS) -> BBox:
        """Override method to fetch bounds from collection metadata."""
        if collections := self.input.get("collections", []):
            if len(collections) == 1:
                collection = self._get_collection(collections[0])
                if collection.extent.spatial:
                    if collection.extent.spatial.bboxes[0]:
                        print(collection.extent.spatial.bboxes[0])
                        self.bounds = list(collection.extent.spatial.bboxes[0])
                        self.crs = WGS84_CRS

        return super().get_geographic_bounds(crs)

    def info(self) -> MosaicInfo:  # type: ignore
        """Mosaic info."""
        renders = {}
        bounds = self.bounds
        crs = self.crs

        if collections := self.input.get("collections", []):
            if len(collections) == 1:
                collection = self._get_collection(collections[0])
                if collection.extent.spatial:
                    bounds = tuple(collection.extent.spatial.bboxes[0])
                    crs = WGS84_CRS
                renders = collection.extra_fields.get("renders", {})

        return MosaicInfo(
            bounds=bounds, crs=CRS_to_uri(crs) or crs.to_wkt(), renders=renders
        )
