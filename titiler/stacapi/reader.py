"""Custom STAC reader."""

from typing import Any, Dict, Optional, Set, Type

import attr
import pystac
import rasterio
from morecantile import TileMatrixSet
import planetary_computer
from rasterio.crs import CRS
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.errors import InvalidAssetName
from rio_tiler.io import BaseReader, Reader, stac
from rio_tiler.types import AssetInfo

from titiler.stacapi.settings import STACSettings
from titiler.stacapi.settings import STACAPISettings

stac_config = STACSettings()
stac_api_config = STACAPISettings()

@attr.s
class STACReader(stac.STACReader):
    """Custom STAC Reader.

    Only accept `pystac.Item` as input (while rio_tiler.io.STACReader accepts url or pystac.Item)

    """

    input: pystac.Item = attr.ib()

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)
    minzoom: int = attr.ib()
    maxzoom: int = attr.ib()

    geographic_crs: CRS = attr.ib(default=WGS84_CRS)

    include_assets: Optional[Set[str]] = attr.ib(default=None)
    exclude_assets: Optional[Set[str]] = attr.ib(default=None)

    include_asset_types: Set[str] = attr.ib(default=stac.DEFAULT_VALID_TYPE)
    exclude_asset_types: Optional[Set[str]] = attr.ib(default=None)

    reader: Type[BaseReader] = attr.ib(default=Reader)
    reader_options: Dict = attr.ib(factory=dict)

    fetch_options: Dict = attr.ib(factory=dict)

    ctx: Any = attr.ib(default=rasterio.Env)

    item: pystac.Item = attr.ib(init=False)

    def __attrs_post_init__(self):
        """Fetch STAC Item and get list of valid assets."""
        self.item = self.input
        super().__attrs_post_init__()

    @minzoom.default
    def _minzoom(self):
        return self.tms.minzoom

    @maxzoom.default
    def _maxzoom(self):
        return self.tms.maxzoom

    def _get_asset_info(self, asset: str) -> AssetInfo:
        """Validate asset names and return asset's url.

        Args:
            asset (str): STAC asset name.

        Returns:
            str: STAC asset href.

        """
        if asset not in self.assets:
            raise InvalidAssetName(
                f"'{asset}' is not valid, should be one of {self.assets}"
            )

        asset_info = self.item.assets[asset]
        extras = asset_info.extra_fields

        url = asset_info.get_absolute_href() or asset_info.href
        # No caching of this should be necessary. From the docs https://planetarycomputer.microsoft.com/docs/concepts/sas/#planetary-computer-python-package:
        # A cache is also kept, which tracks expiration values, to ensure new SAS tokens are only requested when needed.
        # We only want to sign requests to MS PC API. Other ways to handle this could be:
        # 1. Check the asset's URL to see if contains 'blob.core.windows.net' (seems brittle)
        # 2. Set a boolean in settings, something like "SIGN_REQUESTS"
        # 3. Just assume all requests are to MS PC API and sign them. Stub out this function in tests and/or when ENV=test
        if stac_api_config.stac_api_url == stac_api_config.mspc_default_api_url:
            url = planetary_computer.sign(url)

        info = AssetInfo(
            url=url,
            metadata=extras,
        )

        if head := extras.get("file:header_size"):
            info["env"] = {"GDAL_INGESTED_BYTES_AT_OPEN": head}

        if bands := extras.get("raster:bands"):
            stats = [
                (b["statistics"]["minimum"], b["statistics"]["maximum"])
                for b in bands
                if {"minimum", "maximum"}.issubset(b.get("statistics", {}))
            ]
            if len(stats) == len(bands):
                info["dataset_statistics"] = stats

        return info
