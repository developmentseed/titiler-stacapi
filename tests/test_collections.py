"""Test titiler.stacapi collections endpoints."""

import json
import os
from unittest.mock import patch

from .conftest import mock_rasterio_open

item_json = os.path.join(
    os.path.dirname(__file__), "fixtures", "20200307aC0853900w361030.json"
)


@patch("titiler.stacapi.factory.STACAPIBackend.get_assets")
@patch("rio_tiler.io.rasterio.rasterio")
def test_stac_collections(rio, get_assets, app):
    """test STAC items endpoints."""
    rio.open = mock_rasterio_open

    with open(item_json, "r") as f:
        get_assets.return_value = [json.loads(f.read())]

    response = app.get(
        "/collections/noaa-emergency-response/tiles/WebMercatorQuad/15/8589/12849.png",
        params={
            "assets": "cog",
            "datetime": "2024-01-01",
        },
    )
    assert response.status_code == 200

    response = app.get(
        "/collections/noaa-emergency-response/WebMercatorQuad/tilejson.json",
        params={
            "assets": "cog",
            "minzoom": 12,
            "maxzoom": 14,
        },
    )
    assert response.status_code == 200
    resp = response.json()
    assert resp["minzoom"] == 12
    assert resp["maxzoom"] == 14
    assert "?assets=cog" in resp["tiles"][0]


@patch("titiler.stacapi.backend.ItemSearch")
def test_stac_collections_filter(items_search, app):
    """test arguments passed to ItemSearch."""

    class ItemSearch:
        def __init__(self, *args, **kwargs):
            pass

        def items_as_dicts(self):
            return [{}]

    items_search.return_value = ItemSearch()
    _ = app.get(
        "/collections/noaa-emergency-response/tiles/WebMercatorQuad/0/0/0/assets",
        params={
            "filter": json.dumps({"op": "=", "args": [{"property": "value"}, "1"]}),
            "filter-lang": "cql2-json",
        },
    )
    assert items_search.call_args[1]["filter"] == {
        "op": "=",
        "args": [{"property": "value"}, "1"],
    }
    assert items_search.call_args[1]["filter_lang"] == "cql2-json"

    _ = app.get(
        "/collections/noaa-emergency-response/tiles/WebMercatorQuad/0/0/0/assets",
        params={
            "filter": "(value = '1')",
            "filter-lang": "cql2-text",
        },
    )
    assert items_search.call_args[1]["filter"] == "(value = '1')"
    assert items_search.call_args[1]["filter_lang"] == "cql2-text"
