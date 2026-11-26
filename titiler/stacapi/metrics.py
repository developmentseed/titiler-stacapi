"""Optional Prometheus metrics for the default application."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from weakref import WeakSet

from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info

if TYPE_CHECKING:
    from fastapi import FastAPI

_INSTRUMENTED_APPS: WeakSet[FastAPI] = WeakSet()

# Rules are matched, in order, against the route *template* (e.g.
# `/collections/{collection_id}/items/{item_id}/tiles/...`), never against the
# requested URL, so collection/item IDs and layer names cannot leak into labels.
_ROUTE_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^/$"), "landing"),
    (re.compile(r"^/conformance$"), "conformance"),
    (re.compile(r"^/api(\.html)?$"), "docs"),
    (re.compile(r"^/wmts$|/WMTSCapabilities\.xml$"), "wmts"),
    (re.compile(r"^/wms$"), "wms"),
    (re.compile(r"^/layers/"), "layers"),
    (re.compile(r"/tilejson\.json$"), "tilejson"),
    (re.compile(r"/map\.html$"), "map"),
    # before tiles/point/bbox: `.../tiles/{z}/{x}/{y}/assets` only lists assets
    (re.compile(r"/assets$"), "assets"),
    (re.compile(r"/(asset_)?statistics$"), "statistics"),
    (re.compile(r"/tiles(/|$)"), "tiles"),
    (re.compile(r"/point/"), "point"),
    (re.compile(r"/bbox/"), "bbox"),
    (re.compile(r"/feature(/|\.|$)"), "feature"),
    (re.compile(r"/preview(/|\.|$)"), "preview"),
    (re.compile(r"/info(\.geojson)?$"), "info"),
    (re.compile(r"^/tileMatrixSets"), "tms"),
    (re.compile(r"^/algorithms"), "algorithms"),
    (re.compile(r"^/colorMaps"), "colormaps"),
]


def resolve_operation(route: str | None) -> str:
    """Map a route template to a low-cardinality operation label."""
    if not route or route == "none":
        return "unknown"

    for pattern, operation in _ROUTE_RULES:
        if pattern.search(route):
            return operation

    return "other"


# Standard methods are kept as-is; anything else is folded into "other" so
# arbitrary client-supplied method tokens cannot create new label values.
_KNOWN_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"})


def normalize_method(method: str) -> str:
    """Map an HTTP method to a bounded label value."""
    method = method.upper()
    return method if method in _KNOWN_METHODS else "other"


REQUESTS = Counter(
    "titiler_stacapi_http_requests_total",
    "Total HTTP requests by operation.",
    labelnames=("operation", "method", "status"),
)
LATENCY = Histogram(
    "titiler_stacapi_http_request_duration_seconds",
    "HTTP request latency by operation.",
    labelnames=("operation", "method"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)


def record_service_metrics(info: Info) -> None:
    """Record request count and latency using low-cardinality operation labels."""
    # `modified_handler` is the route template resolved by the instrumentator
    # itself. Unlike `scope["route"]`, it is also set for plain Starlette routes
    # (e.g. the OpenAPI/docs pages) and for requests answered before routing
    # (e.g. CORS preflights, which resolve to the route they target).
    operation = resolve_operation(info.modified_handler)
    method = normalize_method(info.method)

    REQUESTS.labels(operation, method, info.modified_status).inc()
    LATENCY.labels(operation, method).observe(info.modified_duration)


def instrument_app(app: FastAPI, endpoint: str = "/metrics") -> None:
    """Instrument a FastAPI app and expose Prometheus metrics."""
    if app in _INSTRUMENTED_APPS:
        return

    (
        Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            excluded_handlers=[r"^/healthz$", rf"^{re.escape(endpoint)}$"],
        )
        .add(record_service_metrics)
        .instrument(app)
        .expose(app, endpoint=endpoint, include_in_schema=False)
    )

    _INSTRUMENTED_APPS.add(app)
