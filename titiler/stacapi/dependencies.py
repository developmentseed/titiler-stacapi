"""titiler-stacapi dependencies."""

import json
from typing import Dict, List, Literal, Optional, TypedDict, get_args

import pystac
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from fastapi import Depends, HTTPException, Path, Query
from pystac_client import ItemSearch
from pystac_client.stac_api_io import StacApiIO
from starlette.requests import Request
from typing_extensions import Annotated
from urllib3 import Retry

from titiler.stacapi.enums import MediaType
from titiler.stacapi.settings import CacheSettings, RetrySettings

ResponseType = Literal["json", "html"]

cache_config = CacheSettings()
retry_config = RetrySettings()


def accept_media_type(accept: str, mediatypes: List[MediaType]) -> Optional[MediaType]:
    """Return MediaType based on accept header and available mediatype.

    Links:
    - https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
    - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept

    """
    accept_values = {}
    for m in accept.replace(" ", "").split(","):
        values = m.split(";")
        if len(values) == 1:
            name = values[0]
            quality = 1.0
        else:
            name = values[0]
            groups = dict([param.split("=") for param in values[1:]])  # type: ignore
            try:
                q = groups.get("q")
                quality = float(q) if q else 1.0
            except ValueError:
                quality = 0

        # if quality is 0 we ignore encoding
        if quality:
            accept_values[name] = quality

    # Create Preference matrix
    media_preference = {
        v: [n for (n, q) in accept_values.items() if q == v]
        for v in sorted(set(accept_values.values()), reverse=True)
    }

    # Loop through available compression and encoding preference
    for _, pref in media_preference.items():
        for media in mediatypes:
            if media.value in pref:
                return media

    # If no specified encoding is supported but "*" is accepted,
    # take one of the available compressions.
    if "*" in accept_values and mediatypes:
        return mediatypes[0]

    return None


def OutputType(
    request: Request,
    f: Annotated[
        Optional[ResponseType],
        Query(
            description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
        ),
    ] = None,
) -> Optional[MediaType]:
    """Output MediaType: json or html."""
    if f:
        return MediaType[f]

    accepted_media = [MediaType[v] for v in get_args(ResponseType)]
    return accept_media_type(request.headers.get("accept", ""), accepted_media)


class APIParams(TypedDict, total=False):
    """STAC API Parameters."""

    api_url: str
    headers: Optional[Dict]


def STACApiParams(
    request: Request,
) -> APIParams:
    """Return STAC API Parameters."""
    return APIParams(
        api_url=request.app.state.stac_url,
    )


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
    headers: Optional[Dict] = None,
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
    collection_id: Annotated[
        str,
        Path(description="STAC Collection Identifier"),
    ],
    item_id: Annotated[str, Path(description="STAC Item Identifier")],
    api_params=Depends(STACApiParams),
) -> pystac.Item:
    """STAC Item dependency for the MultiBaseTilerFactory."""
    return get_stac_item(
        api_params["api_url"],
        collection_id,
        item_id,
        headers=api_params.get("headers", {}),
    )


def STACSearchParams(
    request: Request,
    collection_id: Annotated[
        str,
        Path(description="STAC Collection Identifier"),
    ],
    ids: Annotated[Optional[str], Query(description="Filter by Ids.")] = None,
    bbox: Annotated[
        Optional[str],
        Query(description="Spatial Filter."),
    ] = None,
    datetime: Annotated[Optional[str], Query(description="Temporal Filter.")] = None,
    # sortby: Annotated[
    #     Optional[str],
    #     Query(
    #         description="Column Sort the items by Column (ascending (default) or descending).",
    #     ),
    # ] = None,
    # query: Annotated[
    #     Optional[str], Query(description="CQL2 Filter", alias="filter")
    # ] = None,
    # filter_lang: Annotated[
    #     Optional[Literal["cql2-text", "cql2-json"]],
    #     Query(
    #         description="CQL2 Language (cql2-text, cql2-json). Defaults to cql2-text.",
    #         alias="filter-lang",
    #     ),
    # ] = None,
    limit: Annotated[
        Optional[int],
        Query(description="Limit the number of items per page search (default: 10)"),
    ] = None,
    max_items: Annotated[
        Optional[int],
        Query(description="Limit the number of total items (default: 100)"),
    ] = None,
) -> Dict:
    """Dependency to construct STAC API Search Query."""
    return {
        "collections": [collection_id],
        "ids": ids.split(",") if ids else None,
        "bbox": list(map(float, bbox.split(","))) if bbox else None,
        "datetime": datetime,
        # "sortby": sortby,
        # "filter": query,
        # "filter-lang": filter_lang,
        "limit": limit or 10,
        "max_items": max_items or 100,
    }
