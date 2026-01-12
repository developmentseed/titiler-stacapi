"""test titiler-stacapi mosaic backend."""

import json
import os
from unittest.mock import patch

from geojson_pydantic import Polygon

from titiler.stacapi.backend import STACAPIBackend
from titiler.stacapi.dependencies import APIParams, Search

from .conftest import mock_rasterio_open

item_json = os.path.join(
    os.path.dirname(__file__), "fixtures", "20200307aC0853900w361030.json"
)


@patch("rio_tiler.io.rasterio.rasterio")
@patch("titiler.stacapi.backend.STACAPIBackend.get_assets")
def test_stac_backend(get_assets, rio):
    """test STACAPIBackend."""
    rio.open = mock_rasterio_open

    with open(item_json, "r") as f:
        get_assets.return_value = [json.loads(f.read())]

    with STACAPIBackend(
        input=Search(), api_params=APIParams(url="http://endpoint.stac")
    ) as stac:
        pass

    with STACAPIBackend(
        input=Search(), api_params=APIParams(url="http://endpoint.stac")
    ) as stac:
        assets = stac.assets_for_tile(0, 0, 0)
        assert len(assets) == 1
        assert isinstance(get_assets.call_args.args[0], Polygon)
        assert not get_assets.call_args.kwargs

    with STACAPIBackend(
        input=Search(collections=["col"], ids=["20200307aC0853900w361030"]),
        api_params=APIParams(url="http://endpoint.stac"),
    ) as stac:
        img, assets = stac.tile(
            8589,
            12849,
            15,
            search_options={"limit": 10},
            assets=["cog"],
        )
        assert assets[0] == "noaa-emergency-response/20200307aC0853900w361030"
        assert isinstance(get_assets.call_args.args[0], Polygon)
        assert get_assets.call_args.kwargs["limit"] == 10
        assert img.metadata["timings"]
