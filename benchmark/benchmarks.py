"""Benchmark items."""

import os

import httpx2 as httpx
import pytest

host = os.environ.get("HOST", "0.0.0.0")
port = os.environ.get("PORT", "8081")

tiles = [
    {"tile": "0/0/0", "zoom": 0, "assets": 15},  # 15 Assets
    {"tile": "1/1/1", "zoom": 1, "assets": 6},  # 6 Assets
    {"tile": "2/2/1", "zoom": 2, "assets": 4},  # 4 Assets
    {"tile": "3/5/0", "zoom": 3, "assets": 2},  # 2 Assets
    {"tile": "4/5/9", "zoom": 4, "assets": 1},  # 1 Asset
    {"tile": "5/16/5", "zoom": 5, "assets": 1},  # 1 Asset
    {"tile": "6/43/31", "zoom": 6, "assets": 1},  # 1 Asset
]


@pytest.mark.parametrize("tile", tiles)
def test_benchmark_tile(benchmark, tile):
    """Benchmark /collections tile's endpoint (search+mosaic)."""

    benchmark.name = f"zoom{tile['zoom']}-{tile['assets']}assets"
    benchmark.group = f"Zoom {tile['zoom']} - {tile['assets']} Assets"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/collections/world/tiles/WebMercatorQuad/{t}?assets=asset"
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200


@pytest.mark.parametrize("tile", tiles)
def test_benchmark_search(benchmark, tile):
    """Benchmark assets endpoint (simple search)."""

    benchmark.name = f"zoom{tile['zoom']}"
    benchmark.group = f"Zoom {tile['zoom']}"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/collections/world/tiles/WebMercatorQuad/{t}/assets"
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200
