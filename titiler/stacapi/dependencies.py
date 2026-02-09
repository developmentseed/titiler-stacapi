"""titiler-stacapi dependencies."""

import json
from dataclasses import dataclass, field
from typing import Any, Literal, NotRequired, TypedDict

import pystac
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from fastapi import HTTPException, Path, Query
from pystac_client import ItemSearch
from pystac_client.stac_api_io import StacApiIO
from starlette.requests import Request
from typing_extensions import Annotated
from urllib3 import Retry

from titiler.core.dependencies import DefaultDependency
from titiler.stacapi.settings import CacheSettings, RetrySettings

ResponseType = Literal["json", "html"]

cache_config = CacheSettings()
retry_config = RetrySettings()


class APIParams(TypedDict):
    """STAC API Parameters."""

    url: str
    headers: NotRequired[dict]


class Search(TypedDict, total=False):
    """STAC Search Parameters."""

    collections: list[str] | None
    ids: list[str] | None
    bbox: list[float] | None
    datetime: str | None
    filter: str | dict | None
    filter_lang: Literal["cql2-text", "cql2-json"]


@cached(  # type: ignore
    TTLCache(maxsize=cache_config.maxsize, ttl=cache_config.ttl),
    key=lambda url, collection_id, item_id, headers, **kwargs: hashkey(
        url, collection_id, item_id, json.dumps(headers)
    ),
)
def get_stac_item(
    url: str,
    collection_id: str,
    item_id: str,
    headers: dict | None = None,
) -> pystac.Item:
    """Get STAC Item from STAC API."""
    stac_api_io = StacApiIO(
        max_retries=Retry(
            total=retry_config.retry,
            backoff_factor=retry_config.retry_factor,
        ),
        headers=headers,
    )
    results = ItemSearch(
        f"{url}/search", stac_io=stac_api_io, collections=[collection_id], ids=[item_id]
    )
    items = list(results.items())
    if not items:
        raise HTTPException(
            404,
            f"Could not find Item {item_id} in {collection_id} collection.",
        )

    return items[0]


def ItemIdParams(
    request: Request,
    collection_id: Annotated[
        str,
        Path(description="STAC Collection Identifier"),
    ],
    item_id: Annotated[str, Path(description="STAC Item Identifier")],
) -> pystac.Item:
    """STAC Item dependency for the MultiBaseTilerFactory."""
    # NOTE: here we can customize the forwarded headers to the STAC API,
    # for example to add authentication headers if needed.
    headers: dict[str, Any] = {}
    return get_stac_item(
        request.app.state.stac_url,
        collection_id,
        item_id,
        headers=headers,
    )


def CollectionSearch(
    collection_id: Annotated[
        str,
        Path(description="STAC Collection Identifier."),
    ],
    ids: Annotated[
        str | None,
        Query(
            description="Array of Item ids",
            openapi_examples={
                "user-provided": {"value": None},
                "multiple-items": {"value": "item1,item2"},
            },
        ),
    ] = None,
    bbox: Annotated[
        str | None,
        Query(
            description="Filters items intersecting this bounding box",
            openapi_examples={
                "user-provided": {"value": None},
                "Montreal": {"value": "-73.896103,45.364690,-73.413734,45.674283"},
            },
        ),
    ] = None,
    datetime: Annotated[
        str | None,
        Query(
            description="""Filters items that have a temporal property that intersects this value.\n
Either a date-time or an interval, open or closed. Date and time expressions adhere to RFC 3339. Open intervals are expressed using double-dots.""",
            openapi_examples={
                "user-defined": {"value": None},
                "datetime": {"value": "2018-02-12T23:20:50Z"},
                "closed-interval": {
                    "value": "2018-02-12T00:00:00Z/2018-03-18T12:31:12Z"
                },
                "open-interval-from": {"value": "2018-02-12T00:00:00Z/.."},
                "open-interval-to": {"value": "../2018-03-18T12:31:12Z"},
            },
        ),
    ] = None,
    filter_expr: Annotated[
        str | None,
        Query(
            alias="filter",
            description="""A CQL2 filter expression for filtering items.\n
Supports `CQL2-JSON` as defined in https://docs.ogc.org/is/21-065r2/21-065r2.htmln
Remember to URL encode the CQL2-JSON if using GET""",
            openapi_examples={
                "user-provided": {"value": None},
                "landsat8-item": {
                    "value": "id='LC08_L1TP_060247_20180905_20180912_01_T1_L1TP' AND collection='landsat8_l1tp'"  # noqa: E501
                },
            },
        ),
    ] = None,
    filter_lang: Annotated[
        Literal["cql2-text", "cql2-json"],
        Query(
            alias="filter-lang",
            description="CQL2 Language (cql2-text, cql2-json). Defaults to cql2-text.",
        ),
    ] = "cql2-text",
) -> Search:
    """factory's `path_dependency`"""
    if filter_expr and filter_lang == "cql2-json":
        try:
            filter_expr = json.loads(filter_expr)  # type: ignore
        except json.JSONDecodeError as e:
            raise ValueError("filter expression is not valid JSON") from e

    return Search(
        collections=[collection_id],
        ids=ids.split(",") if ids else None,
        bbox=[float(v) for v in bbox.split(",")] if bbox else None,
        datetime=datetime,
        filter=filter_expr,
        filter_lang=filter_lang,
    )


def SearchParams(
    ids: Annotated[
        str | None,
        Query(
            description="Array of Item ids",
            openapi_examples={
                "user-provided": {"value": None},
                "multiple-items": {"value": "item1,item2"},
            },
        ),
    ] = None,
    bbox: Annotated[
        str | None,
        Query(
            description="Filters items intersecting this bounding box",
            openapi_examples={
                "user-provided": {"value": None},
                "Montreal": {"value": "-73.896103,45.364690,-73.413734,45.674283"},
            },
        ),
    ] = None,
    datetime: Annotated[
        str | None,
        Query(
            description="""Filters items that have a temporal property that intersects this value.\n
Either a date-time or an interval, open or closed. Date and time expressions adhere to RFC 3339. Open intervals are expressed using double-dots.""",
            openapi_examples={
                "user-defined": {"value": None},
                "datetime": {"value": "2018-02-12T23:20:50Z"},
                "closed-interval": {
                    "value": "2018-02-12T00:00:00Z/2018-03-18T12:31:12Z"
                },
                "open-interval-from": {"value": "2018-02-12T00:00:00Z/.."},
                "open-interval-to": {"value": "../2018-03-18T12:31:12Z"},
            },
        ),
    ] = None,
    filter_expr: Annotated[
        str | None,
        Query(
            alias="filter",
            description="""A CQL2 filter expression for filtering items.\n
Supports `CQL2-JSON` as defined in https://docs.ogc.org/is/21-065r2/21-065r2.htmln
Remember to URL encode the CQL2-JSON if using GET""",
            openapi_examples={
                "user-provided": {"value": None},
                "landsat8-item": {
                    "value": "id='LC08_L1TP_060247_20180905_20180912_01_T1_L1TP' AND collection='landsat8_l1tp'"  # noqa: E501
                },
            },
        ),
    ] = None,
    filter_lang: Annotated[
        Literal["cql2-text", "cql2-json"],
        Query(
            alias="filter-lang",
            description="CQL2 Language (cql2-text, cql2-json). Defaults to cql2-text.",
        ),
    ] = "cql2-text",
) -> Search:
    """factory's `path_dependency`"""
    if filter_expr and filter_lang == "cql2-json":
        try:
            filter_expr = json.loads(filter_expr)  # type: ignore
        except json.JSONDecodeError as e:
            raise ValueError("filter expression is not valid JSON") from e

    return Search(
        ids=ids.split(",") if ids else None,
        bbox=[float(v) for v in bbox.split(",")] if bbox else None,
        datetime=datetime,
        filter=filter_expr,
        filter_lang=filter_lang,
    )


@dataclass(init=False)
class BackendParams(DefaultDependency):
    """backend parameters."""

    api_params: APIParams = field(init=False)

    def __init__(self, request: Request):
        """Initialize BackendParams

        Note: Because we don't want `api_params` to appear in the documentation we use a dataclass with a custom `__init__` method.
        FastAPI will use the `__init__` method but will exclude Request in the documentation making `api_params` an invisible dependency.
        """
        self.api_params = APIParams(
            url=request.app.state.stac_url,
            # possibly add headers
        )


@dataclass
class STACAPIExtensionParams(DefaultDependency):
    """STACAPI advanced search parameters: forwared to Backend.get_assets method."""

    sortby: Annotated[
        str | None,
        Query(
            description="An array of property names, prefixed by either '+' for ascending or '-' for descending. If no prefix is provided, '+' is assumed.",
            openapi_examples={
                "user-provided": {"value": None},
                "resolution": {"value": "-gsd"},
                "resolution-and-dates": {"value": "-gsd,-datetime"},
            },
        ),
    ] = None
    limit: Annotated[
        int | None,
        Query(description="Limit the number of items per page search (default: 10)"),
    ] = 10
    max_items: Annotated[
        int | None,
        Query(description="Limit the number of total items (default: 100)"),
    ] = 100

    def __post_init__(self):
        """Post Init."""
        if self.sortby:
            self.sortby = self.sortby.split(",")  # type: ignore
