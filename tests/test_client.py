"""Test titiler.stacapi.client.Client."""

import json
import os
from unittest.mock import PropertyMock, patch

import pystac
import pytest

from titiler.stacapi.client import Client

catalog_json = os.path.join(os.path.dirname(__file__), "fixtures", "catalog.json")


@pytest.fixture
def catalog():
    """Catalog fixture."""
    with open(catalog_json, "r") as f:
        return json.loads(f.read())


@pytest.fixture
def client():
    """STAC client fixture."""
    return Client(
        href="https://myurl.com/catalog.json",
        headers={"Authorization": "Bearer mytoken"},
        max_retries_per_request=3,
    )


def test_get_supported_aggregations(client, catalog):
    """Test supported STAC aggregation methods."""
    links = [pystac.Link.from_dict(link) for link in catalog["links"]]

    with (
        patch.object(Client, "links", new_callable=PropertyMock) as mock_links,
        patch("titiler.stacapi.client.httpx.get") as mock_get,
    ):
        mock_links.return_value = links
        mock_get.return_value.json.return_value = {
            "aggregations": [{"name": "aggregation1"}, {"name": "aggregation2"}]
        }

        supported_aggregations = client.get_supported_aggregations()

    assert supported_aggregations == ["aggregation1", "aggregation2"]
    mock_get.assert_called_once_with(
        "https://stac.endpoint.io/aggregations",
        headers={"Authorization": "Bearer mytoken"},
    )


@patch(
    "titiler.stacapi.client.Client.get_supported_aggregations",
    return_value=["datetime_frequency"],
)
def test_get_aggregation_unsupported(supported_aggregations, client):
    """Test handling of unsupported aggregation types"""
    collection_id = "sentinel-2-l2a"
    aggregation = "unsupported-aggregation"

    with pytest.warns(
        UserWarning, match="Aggregation type unsupported-aggregation is not supported"
    ):
        aggregation_data = client.get_aggregation(collection_id, aggregation)
        assert aggregation_data == []


@patch(
    "titiler.stacapi.client.Client.get_supported_aggregations",
    return_value=["datetime_frequency"],
)
def test_get_aggregation(supported_aggregations, client, catalog):
    """Test handling aggregation response"""
    collection_id = "sentinel-2-l2a"
    aggregation = "datetime_frequency"
    aggregation_params = {"datetime_frequency_interval": "day"}

    links = [pystac.Link.from_dict(link) for link in catalog["links"]]

    with (
        patch.object(Client, "links", new_callable=PropertyMock) as mock_links,
        patch("titiler.stacapi.client.httpx.get") as mock_get,
    ):
        mock_links.return_value = links
        mock_get.return_value.json.return_value = {
            "aggregations": [
                {
                    "name": "datetime_frequency",
                    "buckets": [
                        {
                            "key": "2023-12-11T00:00:00.000Z",
                            "data_type": "frequency_distribution",
                            "frequency": 1,
                            "to": None,
                            "from": None,
                        }
                    ],
                },
                {
                    "name": "unusable_aggregation",
                    "buckets": [
                        {
                            "key": "2023-12-11T00:00:00.000Z",
                        }
                    ],
                },
            ]
        }

        aggregation_data = client.get_aggregation(
            collection_id, aggregation, aggregation_params
        )
        assert aggregation_data[0]["key"] == "2023-12-11T00:00:00.000Z"
        assert aggregation_data[0]["data_type"] == "frequency_distribution"
        assert aggregation_data[0]["frequency"] == 1
        assert len(aggregation_data) == 1


@patch(
    "titiler.stacapi.client.Client.get_supported_aggregations",
    return_value=["datetime_frequency"],
)
def test_get_aggregation_no_response(supported_aggregations, client, catalog):
    """Test handling of no aggregation response"""
    collection_id = "sentinel-2-l2a"
    aggregation = "datetime_frequency"
    aggregation_params = {"datetime_frequency_interval": "day"}

    links = [pystac.Link.from_dict(link) for link in catalog["links"]]

    with (
        patch.object(Client, "links", new_callable=PropertyMock) as mock_links,
        patch("titiler.stacapi.client.httpx.get") as mock_get,
    ):
        mock_links.return_value = links
        mock_get.return_value.json.return_value = {}

        aggregation_data = client.get_aggregation(
            collection_id, aggregation, aggregation_params
        )
    assert aggregation_data == []
