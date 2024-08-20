"""test render extension."""

import json
import os
from unittest.mock import patch

import pystac

from titiler.core import dependencies
from titiler.stacapi.factory import get_dependency_params, get_layer_from_collections

catalog_json = os.path.join(os.path.dirname(__file__), "fixtures", "catalog.json")


@patch("titiler.stacapi.factory.Client")
def test_render(client):
    """test STAC items endpoints."""

    with open(catalog_json, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    collections_render = get_layer_from_collections(
        "https://something.stac", None, None
    )
    assert len(collections_render) == 4

    visual = collections_render["MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual"]
    assert visual["bbox"]
    assert visual["tilematrixsets"]["WebMercatorQuad"]
    assert visual["time"]
    assert visual["render"]["asset_bidx"]

    color = collections_render["MAXAR_BayofBengal_Cyclone_Mocha_May_23_color"]["render"]
    assert isinstance(color["colormap"], str)

    cmap = get_dependency_params(
        dependency=dependencies.ColorMapParams,
        query_params=color,
    )
    assert cmap

    visualr = collections_render["MAXAR_BayofBengal_Cyclone_Mocha_May_23_visualr"][
        "render"
    ]
    assert isinstance(visualr["rescale"][0], str)
    rescale = get_dependency_params(
        dependency=dependencies.RescalingParams,
        query_params=visualr,
    )
    assert rescale
