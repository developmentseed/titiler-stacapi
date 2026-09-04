"""
This module provides an advanced client for interacting with STAC (SpatioTemporal Asset Catalog) APIs.

"""

import sys
import warnings
from typing import Any, cast
from urllib.parse import urlencode

import httpx2 as httpx
import pystac
from attrs import define, field
from rustac import ApiClient

if sys.version_info >= (3, 15):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class Item(TypedDict, extra_items=True):  # type: ignore[call-arg]
    """Simple STAC Item model."""

    id: str
    collection: str
    bbox: tuple[float, float, float, float]
    properties: dict | None
    assets: dict[str, dict[str, Any]]


@define
class Client:
    """Client extends the basic functionality of the pystac.Client class."""

    href: str = field()
    headers: dict = field()
    max_retries_per_request: int = field()

    _client: ApiClient = field(init=False, repr=False)

    def __attrs_post_init__(self):
        """Initialize the ApiClient after the Client is created."""
        self._client = ApiClient(
            href=self.href,
            headers=self.headers,
            max_retries_per_request=self.max_retries_per_request,
        )

    @property
    def links(self) -> list[pystac.Link]:
        """Return the links from the STAC catalog."""
        resp = httpx.get(self.href, headers=self.headers)
        links = resp.json().get("links", [])
        return [pystac.Link.from_dict(link) for link in links]

    def search(self, **params: Any) -> list[pystac.Item]:
        """Return a specific collection from the STAC catalog."""
        items = self._client.search_sync(**params)
        return [pystac.Item.from_dict(item) for item in items]

    def search_as_dict(self, **params: Any) -> list[Item]:
        """Return a specific collection from the STAC catalog."""
        items = self._client.search_sync(**params)
        return [cast(Item, itm) for itm in items]

    def get_item(self, collection_id: str, item_id) -> pystac.Item | None:
        """Return a specific Item from the STAC catalog."""
        items = self._client.search_sync(collections=[collection_id], ids=[item_id])
        if items:
            return pystac.Item.from_dict(items[0])

        return None

    def get_collection(self, collection_id: str) -> pystac.Collection:
        """Return a specific collection from the STAC catalog."""
        collection = self._client.get_collection_sync(collection_id)
        if not collection:
            raise ValueError(f"Collection {collection_id} not found")

        return pystac.Collection.from_dict(collection)

    def get_collections(self) -> list[pystac.Collection]:
        """Return the collections from the STAC catalog."""
        collections = self._client.get_collections_sync()
        return [pystac.Collection.from_dict(collection) for collection in collections]

    def get_aggregation(
        self,
        collection_id: str,
        aggregation: str,
        aggregation_params: dict | None = None,
    ) -> list[dict]:
        """Perform an aggregation on a STAC collection.

        Args:
            collection_id (str): The ID of the collection to aggregate.
            aggregation (str): The aggregation type to perform.
            aggregation_params (Optional[dict], optional): Additional parameters for the aggregation. Defaults to None.
        Returns:
            List[str]: The aggregation response.
        """
        if aggregation not in self.get_supported_aggregations():
            warnings.warn(
                f"Aggregation type {aggregation} is not supported", stacklevel=1
            )
            return []

        # Construct the URL for aggregation
        url = (
            self.href
            + f"/collections/{collection_id}"
            + f"/aggregate?aggregations={aggregation}"
        )
        if aggregation_params:
            params = urlencode(aggregation_params)
            url += f"&{params}"

        aggregation_response = httpx.get(url, headers=self.headers).json()
        if not aggregation_response:
            return []

        aggregation_data = []
        for agg in aggregation_response["aggregations"]:
            if agg["name"] == aggregation:
                aggregation_data = agg["buckets"]

        return aggregation_data

    def get_supported_aggregations(self) -> list[str]:
        """Get the supported aggregation types.

        Returns:
            List[str]: The supported aggregations.
        """
        link = self.get_aggregations_link()
        if not link:
            return []

        response = httpx.get(link.href, headers=self.headers).json()
        aggregations = response.get("aggregations", [])
        return [agg["name"] for agg in aggregations]

    def get_aggregations_link(self) -> pystac.Link | None:
        """Returns this client's aggregations link.

        Returns:
            Optional[pystac.Link]: The aggregations link, or None if there is not one found.
        """
        return next(
            (
                link
                for link in self.links
                if link.rel == "aggregations"
                and link.media_type == pystac.MediaType.JSON
            ),
            None,
        )
