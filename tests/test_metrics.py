"""Test Prometheus metrics endpoint."""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pystac
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from titiler.stacapi.metrics import (
    REQUESTS,
    instrument_app,
    normalize_method,
    resolve_operation,
)

from .conftest import mock_rasterio_open

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
ITEM_JSON = os.path.join(FIXTURES, "20200307aC0853900w361030.json")
COLLECTION_JSON = os.path.join(FIXTURES, "noaa-emergency-response.json")

OPERATIONS = {
    "landing",
    "conformance",
    "wmts",
    "wms",
    "layers",
    "tilejson",
    "map",
    "assets",
    "statistics",
    "tiles",
    "point",
    "bbox",
    "feature",
    "preview",
    "info",
    "tms",
    "algorithms",
    "colormaps",
    "docs",
    "other",
    "unknown",
}

COLL = "/collections/{collection_id}"
ITEM = "/collections/{collection_id}/items/{item_id}"


def _counter_total() -> float:
    """Sum request counter samples across all label sets."""
    total = 0.0
    for metric in REQUESTS.collect():
        for sample in metric.samples:
            if sample.name == "titiler_stacapi_http_requests_total":
                total += sample.value
    return total


@pytest.mark.parametrize(
    "route,expected",
    [
        ("/", "landing"),
        ("/conformance", "conformance"),
        ("/api", "docs"),
        ("/api.html", "docs"),
        # OGC WMTS / WMS
        ("/wmts", "wmts"),
        (f"{COLL}/WMTSCapabilities.xml", "wmts"),
        (f"{ITEM}/WMTSCapabilities.xml", "wmts"),
        ("/wms", "wms"),
        (
            "/layers/{LAYER}/{STYLE}/{TIME}/{TileMatrixSet}/{TileMatrix}/{TileCol}/{TileRow}.{FORMAT}",
            "layers",
        ),
        # Collection (mosaic) endpoints
        (f"{COLL}/info", "info"),
        (f"{COLL}/info.geojson", "info"),
        (f"{COLL}/tiles", "tiles"),
        (f"{COLL}/tiles/{{tileMatrixSetId}}", "tiles"),
        (f"{COLL}/tiles/{{tileMatrixSetId}}/{{z}}/{{x}}/{{y}}", "tiles"),
        (f"{COLL}/tiles/{{tileMatrixSetId}}/{{z}}/{{x}}/{{y}}.{{format}}", "tiles"),
        (f"{COLL}/tiles/{{tileMatrixSetId}}/{{z}}/{{x}}/{{y}}/assets", "assets"),
        (f"{COLL}/{{tileMatrixSetId}}/map.html", "map"),
        (f"{COLL}/{{tileMatrixSetId}}/tilejson.json", "tilejson"),
        (f"{COLL}/point/{{lon}},{{lat}}", "point"),
        (f"{COLL}/point/{{lon}},{{lat}}/assets", "assets"),
        (f"{COLL}/bbox/{{minx}},{{miny}},{{maxx}},{{maxy}}/assets", "assets"),
        # Item endpoints
        (f"{ITEM}/info", "info"),
        (f"{ITEM}/info.geojson", "info"),
        (f"{ITEM}/assets", "assets"),
        (f"{ITEM}/asset_statistics", "statistics"),
        (f"{ITEM}/statistics", "statistics"),
        (f"{ITEM}/tiles", "tiles"),
        (f"{ITEM}/tiles/{{tileMatrixSetId}}/{{z}}/{{x}}/{{y}}.{{format}}", "tiles"),
        (f"{ITEM}/{{tileMatrixSetId}}/map.html", "map"),
        (f"{ITEM}/{{tileMatrixSetId}}/tilejson.json", "tilejson"),
        (f"{ITEM}/point/{{lon}},{{lat}}", "point"),
        (f"{ITEM}/preview", "preview"),
        (f"{ITEM}/preview.{{format}}", "preview"),
        (f"{ITEM}/preview/{{width}}x{{height}}.{{format}}", "preview"),
        (f"{ITEM}/bbox/{{minx}},{{miny}},{{maxx}},{{maxy}}.{{format}}", "bbox"),
        (
            f"{ITEM}/bbox/{{minx}},{{miny}},{{maxx}},{{maxy}}/{{width}}x{{height}}.{{format}}",
            "bbox",
        ),
        (f"{ITEM}/feature", "feature"),
        (f"{ITEM}/feature.{{format}}", "feature"),
        (f"{ITEM}/feature/{{width}}x{{height}}.{{format}}", "feature"),
        # Generic titiler endpoints
        ("/tileMatrixSets", "tms"),
        ("/tileMatrixSets/{tileMatrixSetId}", "tms"),
        ("/algorithms", "algorithms"),
        ("/algorithms/{algorithmId}", "algorithms"),
        ("/colorMaps", "colormaps"),
        ("/colorMaps/{colorMapId}", "colormaps"),
        # Fallbacks
        ("/unknown", "other"),
        ("/healthz", "other"),
        (None, "unknown"),
        ("", "unknown"),
        ("none", "unknown"),
    ],
)
def test_resolve_operation(route, expected):
    """Map routes to low-cardinality operation labels."""
    assert resolve_operation(route) == expected


def test_every_route_has_an_operation(app):
    """Every public route maps to a known operation (new routes need a rule)."""
    paths = app.get("/api").json()["paths"]
    assert paths
    for path in paths:
        if path == "/healthz":
            continue
        operation = resolve_operation(path)
        assert operation in OPERATIONS, path
        assert operation not in {"other", "unknown"}, path


def test_metrics_endpoint_returns_prometheus_output(app):
    """Metrics returns Prometheus exposition with operation labels."""
    assert app.get("/").status_code == 200

    response = app.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "titiler_stacapi_http_requests_total{" in response.text
    assert 'operation="landing"' in response.text
    assert "titiler_stacapi_http_request_duration_seconds_bucket{" in response.text
    assert 'status="2xx"' in response.text


@patch("titiler.stacapi.dependencies.get_stac_item")
@patch("titiler.stacapi.factory.STACAPIBackend._get_collection")
@patch("titiler.stacapi.factory.STACAPIBackend.get_assets")
@patch("rio_tiler.io.rasterio.rasterio")
def test_metrics_labels_do_not_contain_ids(
    rio, get_assets, _get_collection, get_stac_item, app
):
    """Collection and item IDs never end up in label values."""
    rio.open = mock_rasterio_open
    with open(ITEM_JSON) as f:
        item = json.load(f)
    get_assets.return_value = [item]
    get_stac_item.return_value = pystac.Item.from_dict(item)
    _get_collection.return_value = pystac.Collection.from_file(COLLECTION_JSON)

    response = app.get(
        "/collections/noaa-emergency-response/tiles/WebMercatorQuad/15/8589/12849.png",
        params={"assets": "cog", "datetime": "2024-01-01"},
    )
    assert response.status_code == 200

    response = app.get(
        "/collections/noaa-emergency-response/items/20200307aC0853900w361030/assets"
    )
    assert response.status_code == 200

    body = app.get("/metrics").text
    assert 'operation="tiles"' in body
    assert 'operation="assets"' in body
    assert "noaa-emergency-response" not in body
    assert "20200307aC0853900w361030" not in body
    assert "WebMercatorQuad" not in body


@pytest.mark.parametrize(
    "method,expected",
    [
        ("GET", "GET"),
        ("get", "GET"),
        ("HEAD", "HEAD"),
        ("POST", "POST"),
        ("OPTIONS", "OPTIONS"),
        ("PROPFIND", "other"),
        ("FOOBAR", "other"),
    ],
)
def test_normalize_method(method, expected):
    """Non-standard HTTP methods are folded into a single label value."""
    assert normalize_method(method) == expected


def test_metrics_method_label_is_bounded(app):
    """Arbitrary method tokens on a matched route do not become label values."""
    assert app.request("FOOBAR", "/conformance").status_code == 405

    body = app.get("/metrics").text
    assert 'method="FOOBAR"' not in body
    assert 'method="other",operation="conformance",status="4xx"' in body


def test_metrics_cors_preflight_label(app):
    """CORS preflights are labelled with the operation of the targeted route."""
    response = app.options(
        "/collections/abc/info",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200

    body = app.get("/metrics").text
    assert 'method="OPTIONS",operation="info",status="2xx"' in body


def test_metrics_docs_routes_are_labelled(app):
    """OpenAPI/docs pages (plain Starlette routes) are labelled `docs`."""
    assert app.get("/api").status_code == 200
    assert app.get("/api.html").status_code == 200

    body = app.get("/metrics").text
    assert 'method="GET",operation="docs",status="2xx"' in body
    assert 'operation="unknown"' not in body


def test_metrics_exclude_healthz_and_metrics(app):
    """Health and scrape endpoints are not counted under any operation label."""
    before = _counter_total()
    assert app.get("/healthz").status_code == 200
    assert app.get("/metrics").status_code == 200
    assert _counter_total() == before


def test_healthz_exclusion_is_exact():
    """Only the exact /healthz path is excluded from request counters."""
    app = FastAPI()

    @app.get("/foo/healthz-report")
    def healthz_report():
        return {"ok": True}

    instrument_app(app)

    with TestClient(app) as client:
        before = _counter_total()
        assert client.get("/foo/healthz-report").status_code == 200
        assert _counter_total() == before + 1


def test_custom_metrics_endpoint_excluded():
    """A custom scrape endpoint is excluded from request counters."""
    app = FastAPI()

    @app.get("/hello")
    def hello():
        return {"ok": True}

    instrument_app(app, endpoint="/prom")

    with TestClient(app) as client:
        before = _counter_total()
        assert client.get("/prom").status_code == 200
        assert _counter_total() == before

        assert client.get("/hello").status_code == 200
        assert _counter_total() == before + 1
        body = client.get("/prom").text
        assert 'operation="other"' in body


def _run(
    script: str,
    tmp_path: Path,
    env: dict | None = None,
    *,
    base_env: dict | None = None,
    cwd: Path = ROOT,
):
    """Run a python script in a fresh interpreter (module-level state reset)."""
    script_path = tmp_path / "script.py"
    script_path.write_text(textwrap.dedent(script))
    return subprocess.run(
        [sys.executable, str(script_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env={
            **(os.environ if base_env is None else base_env),
            "PYTHONPATH": str(ROOT),
            **(env or {}),
        },
    )


def test_metrics_disabled_by_default(tmp_path: Path):
    """With the flag unset, /metrics is not registered and returns 404."""
    result = _run(
        """
        from starlette.testclient import TestClient

        from titiler.stacapi.main import app

        with TestClient(app) as client:
            assert client.get("/metrics").status_code == 404
        """,
        tmp_path,
        env={"TITILER_STACAPI_STAC_API_URL": "http://something.stac"},
        base_env={k: v for k, v in os.environ.items() if "METRICS_ENABLED" not in k},
        cwd=tmp_path,  # avoid picking up a local .env
    )
    assert result.returncode == 0, result.stderr


def test_multiprocess_metrics_exposition(tmp_path: Path):
    """Multiprocess scrape works when PROMETHEUS_MULTIPROC_DIR is set before import."""
    multiproc_dir = tmp_path / "multiproc"
    multiproc_dir.mkdir()
    result = _run(
        """
        from fastapi import FastAPI
        from starlette.testclient import TestClient

        from titiler.stacapi.metrics import instrument_app

        app = FastAPI()

        @app.get("/")
        def landing():
            return {"ok": True}

        instrument_app(app)

        with TestClient(app) as client:
            assert client.get("/").status_code == 200
            response = client.get("/metrics")
            assert response.status_code == 200
            assert "titiler_stacapi_http_requests_total" in response.text
            assert 'operation="landing"' in response.text
        """,
        tmp_path,
        env={"PROMETHEUS_MULTIPROC_DIR": str(multiproc_dir)},
    )
    assert result.returncode == 0, result.stderr
