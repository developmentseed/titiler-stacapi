"""Custom STAC reader."""

from typing import Any, Sequence, Set, Type
from urllib.parse import urlparse

import attr
import pystac
import rasterio
from morecantile import TileMatrixSet
from rasterio.transform import array_bounds
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.errors import InvalidAssetName, MissingAssets
from rio_tiler.io import BaseReader, MultiBaseReader, Reader
from rio_tiler.io.stac import DEFAULT_VALID_TYPE, STAC_ALTERNATE_KEY, STACReader
from rio_tiler.types import AssetInfo, AssetType


@attr.s
class STACAPIReader(STACReader):
    """Custom STAC Reader.

    Only accept `pystac.Item` as input (while rio_tiler.io.STACReader accepts url or pystac.Item)

    """

    input: pystac.Item = attr.ib()

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)
    minzoom: int = attr.ib(default=None)
    maxzoom: int = attr.ib(default=None)

    include_assets: Set[str] | None = attr.ib(default=None)
    exclude_assets: Set[str] | None = attr.ib(default=None)

    include_asset_types: Set[str] = attr.ib(default=DEFAULT_VALID_TYPE)
    exclude_asset_types: Set[str] | None = attr.ib(default=None)

    assets: Sequence[str] = attr.ib(init=False)
    default_assets: Sequence[AssetType] | None = attr.ib(default=None)

    reader: Type[BaseReader] = attr.ib(default=Reader)
    reader_options: dict = attr.ib(factory=dict)

    ctx: rasterio.Env = attr.ib(default=rasterio.Env)

    # item is a `input` attribute in the rio-tiler `STACReader`
    # we move it outside the `init` method because we will take the `pystac.Item`
    # directly as input.
    item: Any = attr.ib(init=False)
    fetch_options: dict = attr.ib(init=False)

    def __attrs_post_init__(self):
        """set self.item from input."""
        self.item = self.input
        super().__attrs_post_init__()


@attr.s
class SimpleSTACReader(MultiBaseReader):
    """Simplified STAC Reader.

    Inputs should be in form of:
    ```json
    {
        "id": "IAMASTACITEM",
        "collection": "mycollection",
        "bbox": (0, 0, 10, 10),
        "assets": {
            "COG": {
                "href": "https://somewhereovertherainbow.io/cog.tif"
            }
        }
    }
    ```

    """

    input: dict[str, Any] = attr.ib()

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)
    minzoom: int = attr.ib(default=None)
    maxzoom: int = attr.ib(default=None)

    assets: Sequence[str] = attr.ib(init=False)
    default_assets: Sequence[str] | None = attr.ib(default=None)

    reader: Type[BaseReader] = attr.ib(default=Reader)
    reader_options: dict = attr.ib(factory=dict)

    ctx: Any = attr.ib(default=rasterio.Env)

    def __attrs_post_init__(self) -> None:
        """Set reader spatial infos and list of valid assets."""
        self.bounds = self.input["bbox"]
        self.crs = WGS84_CRS  # Per specification STAC items are in WGS84

        if proj := self.input.get("proj"):
            crs_string = proj.get("code") or proj.get("epsg") or proj.get("wkt")
            if all(
                [
                    proj.get("transform"),
                    proj.get("shape"),
                    crs_string,
                ]
            ):
                self.height, self.width = proj.get("shape")
                self.transform = proj.get("transform")
                self.bounds = array_bounds(self.height, self.width, self.transform)
                self.crs = rasterio.crs.CRS.from_string(crs_string)

        self.minzoom = self.minzoom if self.minzoom is not None else self._minzoom
        self.maxzoom = self.maxzoom if self.maxzoom is not None else self._maxzoom

        self.assets = list(self.input["assets"])

        if not self.assets:
            raise MissingAssets(
                "No valid asset found. Asset's media types not supported"
            )

    def _parse_vrt_asset(self, asset: str) -> tuple[str, str | None]:
        if asset.startswith("vrt://") and asset not in self.assets:
            parsed = urlparse(asset)
            if not parsed.netloc:
                raise InvalidAssetName(
                    f"'{asset}' is not valid, couldn't find valid asset"
                )

            if parsed.netloc not in self.assets:
                raise InvalidAssetName(
                    f"'{parsed.netloc}' is not valid, should be one of {self.assets}"
                )

            return parsed.netloc, parsed.query

        return asset, None

    def _get_asset_info(self, asset: AssetType) -> AssetInfo:  # noqa: C901
        """Validate asset names and return asset's url.

        Args:
            asset (str): STAC asset name.

        Returns:
            str: STAC asset href.

        """
        asset_name: str
        if isinstance(asset, dict):
            if not asset.get("name"):
                raise ValueError("asset dictionary does not have `name` key")
            asset_name = asset["name"]
        else:
            asset_name = asset

        asset_name, vrt_options = self._parse_vrt_asset(asset_name)

        if asset_name not in self.assets:
            raise InvalidAssetName(
                f"'{asset_name}' is not valid, should be one of {self.assets}"
            )

        method_options: dict[str, Any] = {}
        reader_options: dict[str, Any] = {}
        if isinstance(asset, dict):
            if indexes := asset.get("indexes"):
                method_options["indexes"] = indexes
            if expr := asset.get("expression"):
                method_options["expression"] = expr

            # TODO: handle `bands` options
            # convert bands to indexes based on the band metadata

        asset_modified = "expression" in method_options or vrt_options

        asset_info = self.input["assets"][asset_name]
        info = {
            "url": asset_info["href"],
            "name": asset_name,
            "media_type": asset_info.get("type"),
            "reader_options": reader_options,
            "method_options": method_options,
        }

        if STAC_ALTERNATE_KEY and "alternate" in asset_info:
            if alternate := asset_info["alternate"].get(STAC_ALTERNATE_KEY):
                info["url"] = alternate["href"]

        if header_size := asset_info.get("file:header_size"):
            info["env"]["GDAL_INGESTED_BYTES_AT_OPEN"] = header_size

        if (bands := asset_info.get("raster:bands")) and not asset_modified:
            stats = [
                (b["statistics"]["minimum"], b["statistics"]["maximum"])
                for b in bands
                if {"minimum", "maximum"}.issubset(b.get("statistics", {}))
            ]
            if len(stats) == len(bands):
                info["dataset_statistics"] = stats

        if vrt_options:
            # Construct VRT url
            info["url"] = f"vrt://{info['url']}?{vrt_options}"

        return info
