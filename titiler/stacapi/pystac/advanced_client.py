"""
This module provides an advanced client for interacting with STAC (SpatioTemporal Asset Catalog) APIs.

The `Client` class extends the basic functionality of the `pystac.Client` to include
methods for retrieving and aggregating data from STAC collections.
"""

import warnings
from typing import Dict, List, Optional
from urllib.parse import urlencode

import pystac
import pystac_client


class Client(pystac_client.Client):
    """Client extends the basic functionality of the pystac.Client class."""

    def get_aggregation(
        self,
        collection_id: str,
        aggregation: str,
        aggregation_params: Optional[Dict] = None,
    ) -> List[Dict]:
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
            self._collections_href(collection_id)
            + f"/aggregate?aggregations={aggregation}"
        )
        if aggregation_params:
            params = urlencode(aggregation_params)
            url += f"&{params}"

        aggregation_response = self._stac_io.read_json(url)

        if not aggregation_response:
            return []

        aggregation_data = []
        for agg in aggregation_response["aggregations"]:
            if agg["name"] == aggregation:
                aggregation_data = agg["buckets"]

        return aggregation_data

    def get_supported_aggregations(self) -> List[str]:
        """Get the supported aggregation types.

        Returns:
            List[str]: The supported aggregations.
        """
        response = self._stac_io.read_json(self.get_aggregations_link())
        aggregations = response.get("aggregations", [])
        return [agg["name"] for agg in aggregations]

    def get_aggregations_link(self) -> Optional[pystac.Link]:
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
