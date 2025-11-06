"""Test Advanced PySTAC client."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from titiler.stacapi.pystac import Client

catalog_json = os.path.join(os.path.dirname(__file__), "fixtures", "catalog.json")


@pytest.fixture
def mock_stac_io():
    """STAC IO mock"""
    return MagicMock()


@pytest.fixture
def client(mock_stac_io):
    """STAC client mock"""
    client = Client(id="pystac-client", description="pystac-client")

    with open(catalog_json, "r") as f:
        catalog = json.loads(f.read())
        client.open = MagicMock()
        client.open.return_value = catalog
        client._collections_href = MagicMock()
        client._collections_href.return_value = "http://example.com/collections"

    client._stac_io = mock_stac_io
    return client


def test_get_supported_aggregations(client, mock_stac_io):
    """Test supported STAC aggregation methods"""
    mock_stac_io.read_json.return_value = {
        "aggregations": [{"name": "aggregation1"}, {"name": "aggregation2"}]
    }
    supported_aggregations = client.get_supported_aggregations()
    assert supported_aggregations == ["aggregation1", "aggregation2"]


@patch(
    "titiler.stacapi.pystac.advanced_client.Client.get_supported_aggregations",
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
    "titiler.stacapi.pystac.advanced_client.Client.get_supported_aggregations",
    return_value=["datetime_frequency"],
)
def test_get_aggregation(supported_aggregations, client, mock_stac_io):
    """Test handling aggregation response"""
    collection_id = "sentinel-2-l2a"
    aggregation = "datetime_frequency"
    aggregation_params = {"datetime_frequency_interval": "day"}

    mock_stac_io.read_json.return_value = {
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
    "titiler.stacapi.pystac.advanced_client.Client.get_supported_aggregations",
    return_value=["datetime_frequency"],
)
def test_get_aggregation_no_response(supported_aggregations, client, mock_stac_io):
    """Test handling of no aggregation response"""
    collection_id = "sentinel-2-l2a"
    aggregation = "datetime_frequency"
    aggregation_params = {"datetime_frequency_interval": "day"}

    mock_stac_io.read_json.return_value = []

    aggregation_data = client.get_aggregation(
        collection_id, aggregation, aggregation_params
    )
    assert aggregation_data == []
