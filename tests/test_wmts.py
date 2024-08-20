"""Test titiler.stacapi Item endpoints."""

import json
import os
from unittest.mock import patch
from urllib.parse import parse_qs

import pystac
import rasterio
from owslib.wmts import WebMapTileService

item_json = os.path.join(
    os.path.dirname(__file__), "fixtures", "46_033111301201_1040010082988200.json"
)
catalog_json = os.path.join(os.path.dirname(__file__), "fixtures", "catalog.json")

DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def mock_rasterio_open(asset):
    """Mock rasterio Open."""
    asset = asset.replace(
        "s3://maxar-opendata/events/BayofBengal-Cyclone-Mocha-May-23/ard/46/033111301201/2023-03-14",
        DATA_DIR,
    )
    return rasterio.open(asset)


@patch("titiler.stacapi.factory.Client")
def test_wmts_getcapabilities(client, app):
    """test STAC items endpoints."""
    with open(catalog_json, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    # Missing Service
    response = app.get("/wmts")
    assert response.status_code == 400

    # Invalid Service
    response = app.get("/wmts", params={"service": "WMS"})
    assert response.status_code == 400

    # Missing Version
    response = app.get("/wmts", params={"service": "WMTS"})
    assert response.status_code == 400

    # Invalid Version
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "2.0.0",
        },
    )
    assert response.status_code == 400

    # Missing Request
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
        },
    )
    assert response.status_code == 400

    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getSomething",
        },
    )
    assert response.status_code == 400

    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getcapabilities",
        },
    )
    assert response.status_code == 200
    wmts = WebMapTileService(url="/wmts", xml=response.text.encode())
    layers = list(wmts.contents)
    assert len(layers) == 4
    assert "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual" in layers
    assert "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color" in layers
    assert "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visualr" in layers
    assert "MAXAR_BayofBengal_Cyclone_Mocha_May_23_cube_dimensions_visual" in layers

    layer = wmts["MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual"]
    assert "WebMercatorQuad" in layer.tilematrixsetlinks
    assert "TIME" in layer.dimensions
    assert ["default"] == list(layer.styles.keys())
    assert ["image/png"] == layer.formats

    params = layer.resourceURLs[0]["template"].split("?")[1]
    query = parse_qs(params)
    assert query["assets"] == ["visual"]
    assert query["asset_bidx"] == ["visual|1,2,3"]

    layer = wmts["MAXAR_BayofBengal_Cyclone_Mocha_May_23_cube_dimensions_visual"]
    assert "TIME" in layer.dimensions
    times = layer.dimensions["TIME"]["values"]
    assert len(times) == 6


@patch("rio_tiler.io.rasterio.rasterio")
@patch("titiler.stacapi.factory.STACAPIBackend.get_assets")
@patch("titiler.stacapi.factory.Client")
def test_wmts_gettile(client, get_assets, rio, app):
    """test STAC items endpoints."""
    rio.open = mock_rasterio_open

    with open(catalog_json, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    with open(item_json, "r") as f:
        get_assets.return_value = [json.loads(f.read())]

    # missing keys
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "gettile",
        },
    )
    assert response.status_code == 400

    # invalid format
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "gettile",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "style": "default",
            "format": "image/yo",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 0,
            "tilerow": 0,
            "tilecol": 0,
        },
    )
    assert response.status_code == 400

    # invalid layer
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "gettile",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_colorrrrrrrrr",
            "style": "",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 0,
            "tilerow": 0,
            "tilecol": 0,
        },
    )
    assert response.status_code == 400
    assert (
        "Invalid 'LAYER' parameter: MAXAR_BayofBengal_Cyclone_Mocha_May_23_colorrrrrrrrr"
        in response.json()["detail"]
    )

    # invalid style
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "gettile",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "style": "something",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 0,
            "tilerow": 0,
            "tilecol": 0,
        },
    )
    assert response.status_code == 400
    assert "Invalid STYLE parameters something" in response.json()["detail"]

    # Missing Time
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "gettile",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "style": "default",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 15,
            "tilerow": 12849,
            "tilecol": 8589,
        },
    )
    assert response.status_code == 400
    assert "Missing 'TIME' parameter" in response.json()["detail"]

    # Invalid Time
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "gettile",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "style": "default",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 15,
            "tilerow": 12849,
            "tilecol": 8589,
            "TIME": "2000-01-01",
        },
    )
    assert response.status_code == 400
    assert "Invalid 'TIME' parameter:" in response.json()["detail"]

    # Invalid TMS
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "gettile",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "style": "default",
            "format": "image/png",
            "tilematrixset": "WebMercatorQua",
            "tilematrix": 15,
            "tilerow": 12849,
            "tilecol": 8589,
            "TIME": "2023-01-05",
        },
    )
    assert response.status_code == 400
    assert "Invalid 'TILEMATRIXSET' parameter" in response.json()["detail"]

    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "gettile",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual",
            "style": "default",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 14,
            "tilerow": 7188,
            "tilecol": 12375,
            "TIME": "2023-01-05",
        },
    )
    assert response.status_code == 200

    response = app.get(
        "/wmts",
        params={
            "SERVICE": "WMTS",
            "VERSION": "1.0.0",
            "REQUEST": "getTile",
            "LAYER": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual",
            "STYLE": "default",
            "FORMAT": "image/png",
            "TILEMATRIXSET": "WebMercatorQuad",
            "TILEMATRIX": 14,
            "TILEROW": 7188,
            "TILECOL": 12375,
            "TIME": "2023-01-05",
        },
    )
    assert response.status_code == 200


@patch("rio_tiler.io.rasterio.rasterio")
@patch("titiler.stacapi.factory.STACAPIBackend.get_assets")
@patch("titiler.stacapi.factory.Client")
def test_wmts_gettile_param_override(client, get_assets, rio, app):
    """test STAC items endpoints."""
    rio.open = mock_rasterio_open

    with open(catalog_json, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    with open(item_json, "r") as f:
        get_assets.return_value = [json.loads(f.read())]

    response = app.get(
        "/wmts",
        params={
            "SERVICE": "WMTS",
            "VERSION": "1.0.0",
            "REQUEST": "getTile",
            "LAYER": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual",
            "STYLE": "default",
            "FORMAT": "image/png",
            "TILEMATRIXSET": "WebMercatorQuad",
            "TILEMATRIX": 14,
            "TILEROW": 7188,
            "TILECOL": 12375,
            "TIME": "2023-01-05",
            "expression": "(where(visual_invalid >= 0))",
        },
    )
    assert response.status_code == 500
    assert "Could not find any valid assets" in response.json()["detail"]

    response = app.get(
        "/wmts",
        params={
            "SERVICE": "WMTS",
            "VERSION": "1.0.0",
            "REQUEST": "getTile",
            "LAYER": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "STYLE": "default",
            "FORMAT": "image/png",
            "TILEMATRIXSET": "WebMercatorQuad",
            "TILEMATRIX": 14,
            "TILEROW": 7188,
            "TILECOL": 12375,
            "TIME": "2023-01-05",
            "colormap": "{invalid}",
        },
    )
    assert response.status_code == 400
    assert "Could not parse the colormap value" in response.json()["detail"]


@patch("rio_tiler.io.rasterio.rasterio")
@patch("titiler.stacapi.factory.STACAPIBackend.get_assets")
@patch("titiler.stacapi.factory.Client")
def test_wmts_getfeatureinfo(client, get_assets, rio, app):
    """test STAC items endpoints."""
    rio.open = mock_rasterio_open

    with open(catalog_json, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    with open(item_json, "r") as f:
        get_assets.return_value = [json.loads(f.read())]

    # missing keys
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getfeatureinfo",
        },
    )
    assert response.status_code == 400

    # invalid infoformat
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getfeatureinfo",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual",
            "style": "",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 0,
            "tilerow": 0,
            "tilecol": 0,
            "TIME": "2023-01-05",
            "infoformat": "application/xml",
            "i": 0,
            "j": 0,
        },
    )
    assert response.status_code == 400
    assert "Invalid 'InfoFormat' parameter:" in response.json()["detail"]

    # invalid layer
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getfeatureinfo",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_colorrrrrrrrr",
            "style": "",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 0,
            "tilerow": 0,
            "tilecol": 0,
            "infoformat": "application/geo+json",
            "i": 0,
            "j": 0,
        },
    )
    assert response.status_code == 400
    assert (
        "Invalid 'LAYER' parameter: MAXAR_BayofBengal_Cyclone_Mocha_May_23_colorrrrrrrrr"
        in response.json()["detail"]
    )

    # invalid style
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getfeatureinfo",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "style": "something",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 0,
            "tilerow": 0,
            "tilecol": 0,
            "infoformat": "application/geo+json",
            "i": 0,
            "j": 0,
        },
    )
    assert response.status_code == 400
    assert "Invalid STYLE parameters something" in response.json()["detail"]

    # Missing Time
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getfeatureinfo",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "style": "default",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 15,
            "tilerow": 12849,
            "tilecol": 8589,
            "infoformat": "application/geo+json",
            "i": 0,
            "j": 0,
        },
    )
    assert response.status_code == 400
    assert "Missing 'TIME' parameter" in response.json()["detail"]

    # Invalid Time
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getfeatureinfo",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "style": "default",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 15,
            "tilerow": 12849,
            "tilecol": 8589,
            "TIME": "2000-01-01",
            "infoformat": "application/geo+json",
            "i": 0,
            "j": 0,
        },
    )
    assert response.status_code == 400
    assert "Invalid 'TIME' parameter:" in response.json()["detail"]

    # Invalid TMS
    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getfeatureinfo",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "style": "default",
            "format": "image/png",
            "tilematrixset": "WebMercatorQua",
            "tilematrix": 15,
            "tilerow": 12849,
            "tilecol": 8589,
            "TIME": "2023-01-05",
            "infoformat": "application/geo+json",
            "i": 0,
            "j": 0,
        },
    )
    assert response.status_code == 400
    assert "Invalid 'TILEMATRIXSET' parameter" in response.json()["detail"]

    response = app.get(
        "/wmts",
        params={
            "service": "WMTS",
            "version": "1.0.0",
            "request": "getfeatureinfo",
            "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual",
            "style": "default",
            "format": "image/png",
            "tilematrixset": "WebMercatorQuad",
            "tilematrix": 14,
            "tilerow": 7188,
            "tilecol": 12375,
            "TIME": "2023-01-05",
            "infoformat": "application/geo+json",
            "i": 0,
            "j": 0,
        },
    )
    assert response.status_code == 200


@patch("rio_tiler.io.rasterio.rasterio")
@patch("titiler.stacapi.factory.STACAPIBackend.get_assets")
@patch("titiler.stacapi.factory.Client")
def test_wmts_gettile_REST(client, get_assets, rio, app):
    """test STAC items endpoints."""
    rio.open = mock_rasterio_open

    with open(catalog_json, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    with open(item_json, "r") as f:
        get_assets.return_value = [json.loads(f.read())]

    # missing keys
    response = app.get(
        "/layers/MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual/default/2023-01-05/WebMercatorQuad/14/12375/7188.png",
        params={
            "assets": ["visual"],
            "asset_bidx": ["visual|1,2,3"],
        },
    )
    assert response.headers["content-type"] == "image/png"
