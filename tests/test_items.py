"""Test titiler.stacapi Item endpoints."""

import json
import os
from unittest.mock import patch

import pystac
import pytest
from httpx import HTTPStatusError, RequestError

from titiler.stacapi.dependencies import get_stac_item

from .conftest import mock_rasterio_open

item_json = os.path.join(
    os.path.dirname(__file__), "fixtures", "20200307aC0853900w361030.json"
)


class MockResponse:
    """Mock HTTX response."""

    def __init__(self, data):
        """init."""
        self.data = data

    def raise_for_status(self):
        """raise_for_status"""
        pass

    @property
    def content(self):
        """return content."""
        return self.data

    def json(self):
        """return json."""
        return json.loads(self.data)


@patch("titiler.stacapi.dependencies.httpx")
def test_get_stac_item(httpx):
    """test get_stac_item."""

    with open(item_json, "r") as f:
        httpx.get.return_value = MockResponse(f.read())
        httpx.HTTPStatusError = HTTPStatusError
        httpx.RequestError = RequestError

    item = get_stac_item(
        "http://endpoint.stac", "noaa-emergency-response", "20200307aC0853900w361030"
    )
    assert isinstance(item, pystac.Item)
    assert item.id == "20200307aC0853900w361030"
    assert item.collection_id == "noaa-emergency-response"


@patch("rio_tiler.io.rasterio.rasterio")
@patch("titiler.stacapi.dependencies.httpx")
def test_stac_items(httpx, rio, app):
    """test STAC items endpoints."""
    rio.open = mock_rasterio_open

    with open(item_json, "r") as f:
        httpx.get.return_value = MockResponse(f.read())
        httpx.HTTPStatusError = HTTPStatusError
        httpx.RequestError = RequestError

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
