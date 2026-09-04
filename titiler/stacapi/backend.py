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
from rasterio.crs import CRS
from rasterio.warp import transform, transform_bounds
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.mosaic.backend import BaseBackend, MosaicInfo
from rio_tiler.types import BBox
from rio_tiler.utils import CRS_to_uri

from .client import Client, Item
from .dependencies import APIParams, Search
from .reader import SimpleSTACReader
from .settings import CacheSettings, ItemsSettings, RetrySettings

cache_config = CacheSettings()
retry_config = RetrySettings()
items_config = ItemsSettings()

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

    def assets_for_tile(self, x: int, y: int, z: int, **kwargs: Any) -> list[Item]:
        """Retrieve assets for tile."""
        bbox = self.tms.bounds(Tile(x, y, z))
        return self.get_assets(Polygon.from_bounds(*bbox), **kwargs)

    def assets_for_point(
        self,
        lng: float,
        lat: float,
        coord_crs: CRS = WGS84_CRS,
        **kwargs: Any,
    ) -> list[Item]:
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
    ) -> list[Item]:
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
    ) -> list[Item]:
        """Find assets."""

        search_query = {
            **self.input,
            "method": "GET" if self.input.get("filter") else "POST",
            "sortby": sortby,
            "limit": limit or items_config.items_per_page,
            "max_items": max_items or items_config.max_items,
        }
        fields = fields or ["assets", "id", "bbox", "collection"]

        params = {
            **search_query,
            "intersects": geom.model_dump_json(exclude_none=True),
            "fields": fields,
        }
        params.pop("bbox", None)

        catalog = Client(
            href=self.api_params["url"],
            headers=self.api_params.get("headers", {}),
            max_retries_per_request=retry_config.retry,
        )
        return catalog.search_as_dict(**params)

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
        catalog = Client(
            href=self.api_params["url"],
            headers=self.api_params.get("headers", {}),
            max_retries_per_request=retry_config.retry,
        )
        return catalog.get_collection(collection_id)

    def get_geographic_bounds(self, crs: CRS) -> BBox:
        """Override method to fetch bounds from collection metadata."""
        if not self.input.get("bbox") and (
            collections := self.input.get("collections", [])
        ):
            if len(collections) == 1:
                collection = self._get_collection(collections[0])
                if collection.extent.spatial:
                    if collection.extent.spatial.bboxes[0]:
                        self.bounds = tuple(collection.extent.spatial.bboxes[0])
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
                if not self.input.get("bbox") and collection.extent.spatial:
                    bounds = tuple(collection.extent.spatial.bboxes[0])
                    crs = WGS84_CRS
                renders = collection.extra_fields.get("renders", {})

        return MosaicInfo(
            bounds=bounds,
            crs=CRS_to_uri(crs) or crs.to_wkt(),
            renders=renders,
        )
