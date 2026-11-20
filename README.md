# titiler-stacapi

<p align="center">
  <img width="800" src="https://github.com/developmentseed/titiler-stacapi/assets/10407788/bb54162e-9a47-4a67-99e5-6dc91098e048">
  <p align="center">Connect titiler to STAC APIs</p>
</p>

<p align="center">
  <a href="https://github.com/developmentseed/titiler-stacapi/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/titiler-stacapi/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://pypi.org/project/titiler-stacapi" target="_blank">
      <img src="https://img.shields.io/pypi/v/titiler-stacapi?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>  
  <a href="https://codecov.io/gh/developmentseed/titiler-stacapi" target="_blank">
      <img src="https://codecov.io/gh/developmentseed/titiler-stacapi/branch/main/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://github.com/developmentseed/titiler-stacapi/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/titiler-stacapi.svg" alt="License">
  </a>
</p>

---

**Documentation**: <a href="https://developmentseed.org/titiler-stacapi/" target="_blank">https://developmentseed.org/titiler-stacapi/</a>

**Source Code**: <a href="https://github.com/developmentseed/titiler-stacapi" target="_blank">https://github.com/developmentseed/titiler-stacapi</a>

---

## Installation

To install from PyPI and run:

```bash
# Make sure you have pip up to date
python -m pip install -U pip
python -m pip  install titiler.stacapi
```

To install from sources and run for development:

We recommand using [`uv`](https://docs.astral.sh/uv) as project manager for development.

See https://docs.astral.sh/uv/getting-started/installation/ for installation 

```bash
git clone https://github.com/developmentseed/titiler-stacapi.git
cd titiler-stacapi

uv sync
```

## Launch

You'll need to have `TITILER_STACAPI_STAC_API_URL` variables set in your environment pointing to your STAC API service.

```
export TITILER_STACAPI_STAC_API_URL=https://api.stac

uv run --extra server uvicorn titiler.stacapi.main:app --port 8000
```

### Using Docker

```
$ git clone https://github.com/developmentseed/titiler-stacapi.git
$ cd titiler-stacapi
$ export TITILER_STACAPI_STAC_API_URL=https://api.stac
$ docker-compose up --build api
```

It runs `titiler.stacapi` using Uvicorn web server.

### How it works

![](https://github.com/developmentseed/titiler-stacapi/assets/10407788/2e53bfe3-402a-4c57-bf61-c055e32f1362)

### WMTS and the Render extension

`titiler-stacapi` makes extensive use of the [**Render**](https://github.com/stac-extensions/render) extension, specifically at the `Collection` level.
By using the render's metadata, the `/wmts` endpoint (from the `OGCEndpointsFactory` factory) can populate a set of `layers` returned by the `GetCapabilities` service.

### Prometheus metrics

Install the optional metrics extra and enable it:

```bash
python -m pip install "titiler.stacapi[metrics]"
export TITILER_STACAPI_API_METRICS_ENABLED=TRUE
```

The published Docker image already ships the `metrics` extra; only the environment variable is needed.

Once enabled, `/metrics` is available on startup and records:

- `titiler_stacapi_http_requests_total{operation,method,status}`
- `titiler_stacapi_http_request_duration_seconds{operation,method}`

`operation` is a low-cardinality label derived from the route template (never from the
requested URL, so collection IDs, item IDs and layer names do not end up in labels):

| operation | routes |
|---|---|
| `landing`, `conformance` | `/`, `/conformance` |
| `tiles` | `.../tiles`, `.../tiles/{tileMatrixSetId}/...` (collection and item) |
| `point`, `bbox`, `feature`, `preview` | `.../point/...`, `.../bbox/...`, `.../feature...`, `.../preview...` |
| `info`, `statistics`, `assets` | `.../info[.geojson]`, `.../[asset_]statistics`, `.../assets` (incl. collection `tiles/.../assets`, `point/.../assets`, `bbox/.../assets`) |
| `tilejson`, `map` | `.../tilejson.json`, `.../map.html` |
| `wmts`, `wms`, `layers` | `/wmts`, `.../WMTSCapabilities.xml`, `/wms`, `/layers/...` |
| `tms`, `algorithms`, `colormaps` | `/tileMatrixSets...`, `/algorithms...`, `/colorMaps...` |
| `other`, `unknown` | any other route / no matched route |

`status` is grouped (`2xx`, `3xx`, `4xx`, `5xx`). `/healthz` and the scrape endpoint are
excluded from request counters. Untemplated paths (for example bare 404s) are also ignored.

With `TITILER_STACAPI_API_METRICS_ENABLED` left at its default (`FALSE`), `/metrics` is not
registered even if the extra is installed.

#### Multi-worker deployments

For multi-worker deployments (for example `uvicorn --workers N`, or Gunicorn as used by the
Docker image with `WEB_CONCURRENCY` > 1), set `PROMETHEUS_MULTIPROC_DIR` to an existing
writable directory **before** the application is imported, and clear that directory before
each server start.

```bash
export PROMETHEUS_MULTIPROC_DIR=/tmp/titiler-stacapi-prometheus
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
rm -rf "$PROMETHEUS_MULTIPROC_DIR"/*
```

With Gunicorn, also mark workers dead on exit so stale metric files are cleaned up:

```python
from prometheus_client import multiprocess


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
```

#### Custom apps

Custom apps can enable the same instrumentation:

```python
from titiler.stacapi.metrics import instrument_app

instrument_app(app)  # or instrument_app(app, endpoint="/custom-metrics")
```


## Contribution & Development

See [CONTRIBUTING.md](https://github.com//developmentseed/titiler-stacapi/blob/main/CONTRIBUTING.md)

## License

See [LICENSE](https://github.com//developmentseed/titiler-stacapi/blob/main/LICENSE)

## Authors

See [contributors](https://github.com/developmentseed/titiler-stacapi/graphs/contributors) for a listing of individual contributors.

## Changes

See [CHANGES.md](https://github.com/developmentseed/titiler-stacapi/blob/main/CHANGES.md).
