# titiler-stacapi

<p align="center">
  <img width="800" src="https://github.com/developmentseed/titiler-stacapi/assets/10407788/bb54162e-9a47-4a67-99e5-6dc91098e048">
  <p align="center">Connect titiler to STAC APIs</p>
</p>

<p align="center">
  <a href="https://github.com/developmentseed/titiler-stacapi/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/titiler-stacapi/workflows/CI/badge.svg" alt="Test">
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

Install from sources and run for development:

```
$ git clone https://github.com/developmentseed/titiler-stacapi.git
$ cd titiler-stacapi
$ python -m pip install -e .
```

## Launch

You'll need to have `TITILER_STACAPI_STAC_API_URL` variables set in your environment pointing to your STAC API service.

```
export TITILER_STACAPI_STAC_API_URL=https://api.stac
```

```
python -m pip install uvicorn

uvicorn titiler.stacapi.main:app --port 8000
```

### Using Docker

```
$ git clone https://github.com/developmentseed/titiler-stacapi.git
$ cd titiler-stacapi
$ docker-compose up --build api
```

It runs `titiler.stacapi` using Gunicorn web server. 

## Contribution & Development

See [CONTRIBUTING.md](https://github.com//developmentseed/titiler-stacapi/blob/main/CONTRIBUTING.md)

## License

See [LICENSE](https://github.com//developmentseed/titiler-stacapi/blob/main/LICENSE)

## Authors

See [contributors](https://github.com/developmentseed/titiler-stacapi/graphs/contributors) for a listing of individual contributors.

## Changes

See [CHANGES.md](https://github.com/developmentseed/titiler-stacapi/blob/main/CHANGES.md).
