"""test render extension."""

import copy
import json
import os
from unittest.mock import patch

import pystac

from titiler.core import dependencies
from titiler.stacapi.dependencies import APIParams
from titiler.stacapi.factory import (
    get_dependency_params,
    get_layer_from_collections,
    get_layers_from_collection,
)

catalog_json = os.path.join(os.path.dirname(__file__), "fixtures", "catalog.json")
catalog_json_old = os.path.join(
    os.path.dirname(__file__), "fixtures", "catalog_old_renders.json"
)


@patch("titiler.stacapi.factory.Client")
def test_render(client):
    """test STAC items endpoints."""

    with open(catalog_json, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    get_layers_from_collection.cache_clear()
    collections_render = get_layer_from_collections(
        APIParams(url="https://something.stac"),
        None,
    )
    assert len(collections_render) == 4

    visual = collections_render["MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual"]
    assert visual["bbox"]
    assert visual["time"]
    assert visual["render"]["assets"]

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
    rendering = get_dependency_params(
        dependency=dependencies.RenderingParams,
        query_params=visualr,
    )
    assert rendering.rescale


@patch("titiler.stacapi.factory.Client")
def test_old_render(client):
    """test STAC items endpoints."""

    with open(catalog_json_old, "r") as f:
        collections = [
            pystac.Collection.from_dict(c) for c in json.loads(f.read())["collections"]
        ]
        client.open.return_value.get_collections.return_value = collections

    get_layers_from_collection.cache_clear()
    collections_render = get_layer_from_collections(
        APIParams(url="https://something.stac"),
        None,
    )
    assert len(collections_render) == 4

    visual = collections_render["MAXAR_BayofBengal_Cyclone_Mocha_May_23_visual"]
    assert visual["bbox"]
    assert visual["time"]
    assert visual["render"]["assets"] == ["visual|bidx=1,2,3"]
    assert "asset_bidx" not in visual["render"]


@patch("titiler.stacapi.factory.Client")
def test_layers_cached_per_collection(client):
    """Layers are cached per collection and not as one big capabilities document."""

    with open(catalog_json, "r") as f:
        collections_dict = json.loads(f.read())["collections"]

    def _collections():
        # a new set of objects is created on each call, like a real STAC API request
        return [pystac.Collection.from_dict(copy.deepcopy(c)) for c in collections_dict]

    client.open.return_value.get_collections.side_effect = lambda: _collections()

    get_layers_from_collection.cache_clear()
    api_params = APIParams(url="https://something.stac")

    first = get_layer_from_collections(api_params, None)
    second = get_layer_from_collections(api_params, None)
    assert first == second

    # the layers are served from the cache, not re-created
    for render_id, layer in first.items():
        assert second[render_id] is layer

    # updating one collection only invalidates the layers of that collection
    collections_dict[0]["renders"]["visual"]["assets"] = ["updated"]

    third = get_layer_from_collections(api_params, None)
    updated_collection_id = collections_dict[0]["id"]
    for render_id, layer in third.items():
        if layer["collection"] == updated_collection_id:
            assert layer is not first[render_id]
        else:
            assert layer is first[render_id]

    assert third[f"{updated_collection_id}_visual"]["render"]["assets"] == ["updated"]
