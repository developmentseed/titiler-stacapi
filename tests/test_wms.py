"""Test titiler.stacapi WMS endpoints."""

import json
import os
from unittest.mock import patch

import pystac
import rasterio
from owslib.wms import WebMapService

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
def test_wms_getcapabilities(client, app):
    """test WMS Get Capabilities endpoints."""
    with open(catalog_json, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    # Missing Service
    response = app.get("/wms")
    assert response.status_code == 400

    # Invalid Service
    response = app.get("/wms", params={"service": "WMS"})
    assert response.status_code == 400

    # Missing Version
    response = app.get("/wms", params={"service": "WMTS"})
    assert response.status_code == 400

    # Invalid Version
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "2.0.0",
        },
    )
    assert response.status_code == 400

    # Missing Request
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
        },
    )
    assert response.status_code == 400

    response = app.get(
        "/wmts",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "getSomething",
        },
    )
    assert response.status_code == 400

    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "getcapabilities",
        },
    )
    assert response.status_code == 200
    wms = WebMapService(url="/wms", xml=response.text.encode(), version="1.3.0")

    assert wms.identification.type == "OGC:WMS"
    assert wms.identification.version == "1.3.0"
    assert [op.name for op in wms.operations] == [
        "GetCapabilities",
        "GetMap",
        "GetFeatureInfo",
    ]
    assert len(wms.getOperationByName("GetMap").methods) == 1
    assert "image/png" in wms.getOperationByName("GetMap").formatOptions

    layers = list(wms.contents)
    assert len(layers) == 4
    assert "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual" in layers
    assert "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color" in layers
    assert "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visualr" in layers
    assert "MAXAR_BayofBengal_Cyclone_Mocha_May_23_cube_dimensions_visual" in layers

    layer = wms["MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual"]
    assert "TIME" in layer.dimensions

    layer = wms["MAXAR_BayofBengal_Cyclone_Mocha_May_23_cube_dimensions_visual"]
    assert "TIME" in layer.dimensions
    times = layer.dimensions["TIME"]["values"]
    assert len(times) == 6


@patch("rio_tiler.io.rasterio.rasterio")
@patch("titiler.stacapi.backend.ItemSearch")
@patch("titiler.stacapi.factory.Client")
def test_wms_getmap(client, item_search, rio, app):
    """test WMS Get Map endpoints."""
    rio.open = mock_rasterio_open

    with open(catalog_json, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    with open(item_json, "r") as f:
        item_search.return_value.items_as_dicts.return_value = [json.loads(f.read())]

    # missing parameters
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "gettile",
        },
    )
    assert response.status_code == 400

    # invalid format
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "getmap",
            "layers": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "bbox": "-4323278.319809569,9532003.17527462,-4322055.327357005,9533226.167727182",
            "CRS": "EPSG:3857",
            "width": 256,
            "height": 256,
            "styles": "default",
            "format": "image/yo",
        },
    )
    assert response.status_code == 400

    # invalid layer
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "getmap",
            "layers": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_colorrrrrrrrr",
            "bbox": "-4323278.319809569,9532003.17527462,-4322055.327357005,9533226.167727182",
            "CRS": "EPSG:3857",
            "width": 256,
            "height": 256,
            "styles": "default",
            "format": "image/png",
        },
    )
    assert response.status_code == 400
    assert (
        "Invalid 'LAYER' parameter: MAXAR_BayofBengal_Cyclone_Mocha_May_23_colorrrrrrrrr"
        in response.json()["detail"]
    )

    # invalid style
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetMap",
            "layers": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "bbox": "-4323278.319809569,9532003.17527462,-4322055.327357005,9533226.167727182",
            "CRS": "EPSG:3857",
            "width": 256,
            "height": 256,
            "styles": "something",
            "format": "image/png",
        },
    )
    assert response.status_code == 400
    assert (
        "Invalid STYLE 'something' for layer MAXAR_BayofBengal_Cyclone_Mocha_May_23_color"
        in response.json()["detail"]
    )

    # invalid bbox
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetMap",
            "layers": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "bbox": "-4323278.319809569,9532003.17527462",
            "CRS": "EPSG:3857",
            "width": 256,
            "height": 256,
            "styles": "",
            "format": "image/png",
        },
    )
    assert response.status_code == 400
    assert "Invalid 'BBOX' parameters" in response.json()["detail"]

    # invalid crs
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetMap",
            "layers": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "bbox": "-4323278.319809569,9532003.17527462,-4322055.327357005,9533226.167727182",
            "CRS": "EPSG:3857dasdas",
            "width": 256,
            "height": 256,
            "styles": "",
            "format": "image/png",
        },
    )
    assert response.status_code == 400
    assert "Invalid 'CRS' parameter" in response.json()["detail"]

    # invalid crs
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetMap",
            "layers": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "bbox": "-4323278.319809569,9532003.17527462,-4322055.327357005,9533226.167727182",
            "CRS": "EPSG:2154 ",
            "width": 256,
            "height": 256,
            "styles": "",
            "format": "image/png",
        },
    )
    assert response.status_code == 400
    assert "Unsupported 'CRS' parameter" in response.json()["detail"]

    # Missing Time
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetMap",
            "layers": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "bbox": "-4323278.319809569,9532003.17527462,-4322055.327357005,9533226.167727182",
            "CRS": "EPSG:3857 ",
            "width": 256,
            "height": 256,
            "styles": "",
            "format": "image/png",
        },
    )
    assert response.status_code == 400
    assert "Missing 'TIME' parameter" in response.json()["detail"]

    # Invalid Time
    response = app.get(
        "/wms",
        params={
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetMap",
            "layers": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
            "bbox": "-4323278.319809569,9532003.17527462,-4322055.327357005,9533226.167727182",
            "CRS": "EPSG:3857 ",
            "width": 256,
            "height": 256,
            "styles": "",
            "format": "image/png",
            "TIME": "2000-01-01",
        },
    )
    assert response.status_code == 400
    assert "Invalid 'TIME' parameter:" in response.json()["detail"]

    # response = app.get(
    #     "/wms",
    #     params={
    #         "service": "WMS",
    #         "version": "1.3.0",
    #         "request": "GetMap",
    #         "layers": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
    #         "bbox": "-4323278.319809569,9532003.17527462,-4322055.327357005,9533226.167727182",
    #         "CRS": "EPSG:3857 ",
    #         "width": 256,
    #         "height": 256,
    #         "styles": "",
    #         "format": "image/png",
    #         "TIME": "2023-01-05",
    #     },
    # )
    # assert response.status_code == 200
    # assert (
    #     item_search.call_args.kwargs.get("datetime")
    #     == "2023-01-05T00:00:00Z/2023-01-05T23:59:59Z"
    # )


#     response = app.get(
#         "/wmts",
#         params={
#             "SERVICE": "WMTS",
#             "VERSION": "1.0.0",
#             "REQUEST": "getTile",
#             "LAYER": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual",
#             "STYLE": "default",
#             "FORMAT": "image/png",
#             "TILEMATRIXSET": "WebMercatorQuad",
#             "TILEMATRIX": 14,
#             "TILEROW": 7188,
#             "TILECOL": 12375,
#             "TIME": "2023-01-05",
#         },
#     )
#     assert response.status_code == 200
#     assert (
#         item_search.call_args.kwargs.get("datetime")
#         == "2023-01-05T00:00:00Z/2023-01-05T23:59:59Z"
#     )


# @patch("rio_tiler.io.rasterio.rasterio")
# @patch("titiler.stacapi.backend.ItemSearch")
# @patch("titiler.stacapi.factory.Client")
# def test_wmts_gettile_param_override(client, item_search, rio, app):
#     """test STAC items endpoints."""
#     rio.open = mock_rasterio_open

#     with open(catalog_json, "r") as f:
#         collections = [
#             pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
#         ]
#         client.open.return_value.get_collections.return_value = collections

#     with open(item_json, "r") as f:
#         item_search.return_value.items_as_dicts.return_value = [json.loads(f.read())]

#     response = app.get(
#         "/wmts",
#         params={
#             "SERVICE": "WMTS",
#             "VERSION": "1.0.0",
#             "REQUEST": "getTile",
#             "LAYER": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual",
#             "STYLE": "default",
#             "FORMAT": "image/png",
#             "TILEMATRIXSET": "WebMercatorQuad",
#             "TILEMATRIX": 14,
#             "TILEROW": 7188,
#             "TILECOL": 12375,
#             "TIME": "2023-01-05",
#             "expression": "(where(visual_invalid >= 0))",
#         },
#     )
#     assert response.status_code == 500
#     assert "Could not find any valid assets" in response.json()["detail"]

#     response = app.get(
#         "/wmts",
#         params={
#             "SERVICE": "WMTS",
#             "VERSION": "1.0.0",
#             "REQUEST": "getTile",
#             "LAYER": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
#             "STYLE": "default",
#             "FORMAT": "image/png",
#             "TILEMATRIXSET": "WebMercatorQuad",
#             "TILEMATRIX": 14,
#             "TILEROW": 7188,
#             "TILECOL": 12375,
#             "TIME": "2023-01-05",
#             "colormap": "{invalid}",
#         },
#     )
#     assert response.status_code == 400
#     assert "Could not parse the colormap value" in response.json()["detail"]


# @patch("rio_tiler.io.rasterio.rasterio")
# @patch("titiler.stacapi.backend.ItemSearch")
# @patch("titiler.stacapi.factory.Client")
# def test_wmts_getfeatureinfo(client, item_search, rio, app):
#     """test STAC items endpoints."""
#     rio.open = mock_rasterio_open

#     with open(catalog_json, "r") as f:
#         collections = [
#             pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
#         ]
#         client.open.return_value.get_collections.return_value = collections

#     with open(item_json, "r") as f:
#         item_search.return_value.items_as_dicts.return_value = [json.loads(f.read())]

#     # missing keys
#     response = app.get(
#         "/wmts",
#         params={
#             "service": "WMTS",
#             "version": "1.0.0",
#             "request": "getfeatureinfo",
#         },
#     )
#     assert response.status_code == 400

#     # invalid infoformat
#     response = app.get(
#         "/wmts",
#         params={
#             "service": "WMTS",
#             "version": "1.0.0",
#             "request": "getfeatureinfo",
#             "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual",
#             "style": "",
#             "format": "image/png",
#             "tilematrixset": "WebMercatorQuad",
#             "tilematrix": 0,
#             "tilerow": 0,
#             "tilecol": 0,
#             "TIME": "2023-01-05",
#             "infoformat": "application/xml",
#             "i": 0,
#             "j": 0,
#         },
#     )
#     assert response.status_code == 400
#     assert "Invalid 'InfoFormat' parameter:" in response.json()["detail"]

#     # invalid layer
#     response = app.get(
#         "/wmts",
#         params={
#             "service": "WMTS",
#             "version": "1.0.0",
#             "request": "getfeatureinfo",
#             "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_colorrrrrrrrr",
#             "style": "",
#             "format": "image/png",
#             "tilematrixset": "WebMercatorQuad",
#             "tilematrix": 0,
#             "tilerow": 0,
#             "tilecol": 0,
#             "infoformat": "application/geo+json",
#             "i": 0,
#             "j": 0,
#         },
#     )
#     assert response.status_code == 400
#     assert (
#         "Invalid 'LAYER' parameter: MAXAR_BayofBengal_Cyclone_Mocha_May_23_colorrrrrrrrr"
#         in response.json()["detail"]
#     )

#     # invalid style
#     response = app.get(
#         "/wmts",
#         params={
#             "service": "WMTS",
#             "version": "1.0.0",
#             "request": "getfeatureinfo",
#             "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
#             "style": "something",
#             "format": "image/png",
#             "tilematrixset": "WebMercatorQuad",
#             "tilematrix": 0,
#             "tilerow": 0,
#             "tilecol": 0,
#             "infoformat": "application/geo+json",
#             "i": 0,
#             "j": 0,
#         },
#     )
#     assert response.status_code == 400
#     assert "Invalid STYLE parameters something" in response.json()["detail"]

#     # Missing Time
#     response = app.get(
#         "/wmts",
#         params={
#             "service": "WMTS",
#             "version": "1.0.0",
#             "request": "getfeatureinfo",
#             "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
#             "style": "default",
#             "format": "image/png",
#             "tilematrixset": "WebMercatorQuad",
#             "tilematrix": 15,
#             "tilerow": 12849,
#             "tilecol": 8589,
#             "infoformat": "application/geo+json",
#             "i": 0,
#             "j": 0,
#         },
#     )
#     assert response.status_code == 400
#     assert "Missing 'TIME' parameter" in response.json()["detail"]

#     # Invalid Time
#     response = app.get(
#         "/wmts",
#         params={
#             "service": "WMTS",
#             "version": "1.0.0",
#             "request": "getfeatureinfo",
#             "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
#             "style": "default",
#             "format": "image/png",
#             "tilematrixset": "WebMercatorQuad",
#             "tilematrix": 15,
#             "tilerow": 12849,
#             "tilecol": 8589,
#             "TIME": "2000-01-01",
#             "infoformat": "application/geo+json",
#             "i": 0,
#             "j": 0,
#         },
#     )
#     assert response.status_code == 400
#     assert "Invalid 'TIME' parameter:" in response.json()["detail"]

#     # Invalid TMS
#     response = app.get(
#         "/wmts",
#         params={
#             "service": "WMTS",
#             "version": "1.0.0",
#             "request": "getfeatureinfo",
#             "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_color",
#             "style": "default",
#             "format": "image/png",
#             "tilematrixset": "WebMercatorQua",
#             "tilematrix": 15,
#             "tilerow": 12849,
#             "tilecol": 8589,
#             "TIME": "2023-01-05",
#             "infoformat": "application/geo+json",
#             "i": 0,
#             "j": 0,
#         },
#     )
#     assert response.status_code == 400
#     assert "Invalid 'TILEMATRIXSET' parameter" in response.json()["detail"]

#     response = app.get(
#         "/wmts",
#         params={
#             "service": "WMTS",
#             "version": "1.0.0",
#             "request": "getfeatureinfo",
#             "layer": "MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual",
#             "style": "default",
#             "format": "image/png",
#             "tilematrixset": "WebMercatorQuad",
#             "tilematrix": 14,
#             "tilerow": 7188,
#             "tilecol": 12375,
#             "TIME": "2023-01-05",
#             "infoformat": "application/geo+json",
#             "i": 0,
#             "j": 0,
#         },
#     )
#     assert response.status_code == 200


# @patch("rio_tiler.io.rasterio.rasterio")
# @patch("titiler.stacapi.backend.ItemSearch")
# @patch("titiler.stacapi.factory.Client")
# def test_wmts_gettile_REST(client, item_search, rio, app):
#     """test STAC items endpoints."""
#     rio.open = mock_rasterio_open

#     with open(catalog_json, "r") as f:
#         collections = [
#             pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
#         ]
#         client.open.return_value.get_collections.return_value = collections

#     with open(item_json, "r") as f:
#         item_search.return_value.items_as_dicts.return_value = [json.loads(f.read())]

#     # missing keys
#     response = app.get(
#         "/layers/MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual/default/2023-01-05/WebMercatorQuad/14/12375/7188.png",
#         params={
#             "assets": ["visual"],
#             "asset_bidx": ["visual|1,2,3"],
#         },
#     )
#     assert response.headers["content-type"] == "image/png"
