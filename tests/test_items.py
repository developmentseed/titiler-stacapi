"""Test titiler.stacapi Item endpoints."""

import json
import os
from unittest.mock import patch

import pystac
import pytest

from .conftest import mock_rasterio_open

item_json = os.path.join(
    os.path.dirname(__file__), "fixtures", "20200307aC0853900w361030.json"
)


@patch("rio_tiler.io.rasterio.rasterio")
@patch("titiler.stacapi.dependencies.get_stac_item")
def test_stac_items(get_stac_item, rio, app):
    """test STAC items endpoints."""
    rio.open = mock_rasterio_open

    with open(item_json, "r") as f:
        get_stac_item.return_value = pystac.Item.from_dict(json.loads(f.read()))

    response = app.get(
        "/collections/noaa-emergency-response/items/20200307aC0853900w361030/assets",
    )
    assert response.status_code == 200
    assert response.json() == ["cog"]

    with pytest.warns(UserWarning):
        response = app.get(
            "/collections/noaa-emergency-response/items/20200307aC0853900w361030/info",
        )
    assert response.status_code == 200
    assert response.json()["cog"]

    response = app.get(
        "/collections/noaa-emergency-response/items/20200307aC0853900w361030/info",
        params={"assets": "cog"},
    )
    assert response.status_code == 200
    assert response.json()["cog"]
