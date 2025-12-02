"""test get_dependency_params."""

from titiler.core.dependencies import RenderingParams
from titiler.stacapi.dependencies import SearchParams, STACAPIExtensionParams
from titiler.stacapi.factory import get_dependency_params


def test_get_params_rescale():
    """test get_dependency_params for rescale."""

    def _parse_rescale(rescale):
        rescales = []
        for r in qs["rescale"]:
            if not isinstance(r, str):
                rescales.append(",".join(map(str, r)))
            else:
                rescales.append(r)

        return rescales

    qs = {"rescale": ["0,1", "2,3"]}
    assert get_dependency_params(
        dependency=RenderingParams,
        query_params={"rescale": _parse_rescale(qs)},
    ).rescale == [(0.0, 1.0), (2.0, 3.0)]

    qs = {"rescale": [[0, 1], [2, 3]]}
    assert get_dependency_params(
        dependency=RenderingParams,
        query_params={"rescale": _parse_rescale(qs)},
    ).rescale == [(0.0, 1.0), (2.0, 3.0)]


def test_get_params_stacquery():
    """test get_dependency_params for STACQueryParams."""
    qs = {
        "bbox": "1,2,3,4",
        "datetime": "2020-01-01/2020-12-31",
        "limit": 10,
        "max_items": 100,
    }
    assert get_dependency_params(
        dependency=SearchParams,
        query_params=qs,
    ) == {
        "ids": None,
        "bbox": [1.0, 2.0, 3.0, 4.0],
        "datetime": "2020-01-01/2020-12-31",
        "filter_expr": None,
        "filter_lang": "cql2-text",
    }
    assert get_dependency_params(
        dependency=STACAPIExtensionParams,
        query_params=qs,
    ).as_dict(exclude_none=False) == {
        "limit": 10,
        "max_items": 100,
        "sortby": None,
    }

    qs = {
        "ids": "a,b,c",
        "bbox": "1,2,3,4",
        "datetime": "2020-01-01/2020-12-31",
        "filter": "property=value",
        "limit": 100,
        "max_items": 1000,
        "sortby": "-gsg,yo",
    }
    assert get_dependency_params(
        dependency=SearchParams,
        query_params=qs,
    ) == {
        "ids": ["a", "b", "c"],
        "bbox": [1.0, 2.0, 3.0, 4.0],
        "datetime": "2020-01-01/2020-12-31",
        "filter_expr": "property=value",
        "filter_lang": "cql2-text",
    }
    assert get_dependency_params(
        dependency=STACAPIExtensionParams,
        query_params=qs,
    ).as_dict(exclude_none=False) == {
        "limit": 100,
        "max_items": 1000,
        "sortby": ["-gsg", "yo"],
    }
