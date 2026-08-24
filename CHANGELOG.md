## [2.1.1](https://github.com/developmentseed/titiler-stacapi/compare/2.1.0...2.1.1) (2026-08-24)


### Bug Fixes

* bench names ([2a51701](https://github.com/developmentseed/titiler-stacapi/commit/2a517015a965755b22aef0f2ea4b79042a9a2626))
* cache ([a4951aa](https://github.com/developmentseed/titiler-stacapi/commit/a4951aa1d9a055f2e8b886958288354d46ee92d1))
* changelog link ([7533d7f](https://github.com/developmentseed/titiler-stacapi/commit/7533d7f7e629d325531c46058eba676bf1a07551))
* disable cache ([1bee9a0](https://github.com/developmentseed/titiler-stacapi/commit/1bee9a033f7db4aa0c4b0de9bc544962b50181f3))
* fix dependabot limitation of parsing only FROM lines in docker image ([df6a4c7](https://github.com/developmentseed/titiler-stacapi/commit/df6a4c72f81924da2dd9a8304bb882db2181e72d))
* fix dependabot limitation of parsing only FROM lines in docker images ([befc089](https://github.com/developmentseed/titiler-stacapi/commit/befc08909e466959c21a6b491d5f6aaae1e88675))
* install psycopg ([97c0d91](https://github.com/developmentseed/titiler-stacapi/commit/97c0d91b7ea78be108ce117663d2fc1ad3127813))
* install psycopg ([87ae97a](https://github.com/developmentseed/titiler-stacapi/commit/87ae97a52b39f83080bdeb6fd178717a7b9982a5))


### Code Refactoring

* use wolfi docker image ([a6d0ac9](https://github.com/developmentseed/titiler-stacapi/commit/a6d0ac94205d104bcf34a5662558da7ce3cf855a))
* use wolfi docker image ([16d06ea](https://github.com/developmentseed/titiler-stacapi/commit/16d06eace6384f414187f5f7d5dc0697c9d4bd4e))

## [Unreleased]

## [2.1.0] - 2026-07-29

* feat: update titiler-* requirements to >=2.2,<2.3

## [2.0.3] - 2026-07-29

* chore: add benchmark
* fix: add `user` in docker image
* fix: httpx2 dependency
* fix: set upper limit for fastapi to avoid breaking change in openapi tools 
* change: refactor Dockerfile to use uv lock file 

## [2.0.2] - 2026-04-10

* fix: update render configuration (to titiler 2.0 format) when fetching render metadata from collections in `OGCEndpointsFactory`

## [2.0.1] - 2026-04-07

* add: env settings to configure MaxItems and ItemsPerPage options for STAC API Backend
    - `TITILER_STACAPI_ITEMS_PER_PAGE`: set number of items `per-page` returned for Search request (defaults to 10)
    - `TITILER_STACAPI_MAX_ITEMS`: set max items returned by a Search request (defaults to 100)

## [2.0.0] - 2026-03-16

* change: titiler-* requirements to >=2.0,<2.1
* change: asset notation to `assets={name}|{options=...}` 
* remove `vrt:` asset notation

## [1.1.3] - 2026-03-05

* fix: better handling of custom TMS ids in WMTS endpoints
* fix: CQL filter expression support in ItemSearch requests
* remove: orjson (pydantic now serializes the model faster than orjson)
* remove: `cacert.org` certificats updates in Docker image

## [1.1.2] - 2026-02-12

* fix: render's parameter handling and query-parameter override

## [1.1.1] - 2026-02-09

* fix: `APIParams` type to make URL a required key

## [1.1.0] - 2026-02-09

* add: OGC Web Map Server Implementation Specification `/wms` endpoint

## [1.0.0] - 2026-02-06

* update titiler requirements to `>=1.0,<1.1`
* add support for python 3.14
* update type hints for python >=3.11
* move and rename `titiler.stacapi.backend.CustomSTACReader` to `titiler.stacapi.reader.SimpleSTACReader`
* delete `utils` sub-module (utility functions have been moved to `titiler.core`)
* rename `titiler.stacapi.reader.STACReader` to `STACAPIReader`
* add `ids`, `filter-lang` and `filter` parameters to collection's queries
* refactor `STACAPIBackend` to use rio-tiler's mosaic backend
* add `/conformance` endpoint
* replace `/debug` endpoint by `/healthz`
* add more links to the landing page
* add WMTS extensions to the Items and Collections endpoints
* remove custom `MosaicTilerFactory` and default to the one from `titiler.mosaic`
* remove unused `STACSettings`. Alternate HREF key env needs to be defined using `RIO_TILER_STAC_ALTERNATE_KEY`

## [0.4.0] - 2025-11-06

* switch to `uv` for development
* switch to `hatch` for python package build-system
* add support for python version 3.13
* bump minimum python version to 3.11
* update docker image to python:3.13
* Upgrade to become compatible with titiler.core/titiler.mosaic v0.19 (author @jverrydt, https://github.com/developmentseed/titiler-stacapi/pull/32)

## [0.3.3] - 2025-11-06

* fix single date query to only select one day (author @wschoors, https://github.com/developmentseed/titiler-stacapi/pull/34)

## [0.3.2] - 2025-05-19

* Align ows:Title, Identifier and Abstract in WMTS GetCapabilities (author @jverrydt, https://github.com/developmentseed/titiler-stacapi/pull/31)

## [0.3.1] - 2025-02-25

* use only cql2-text for GET request filter parameter (author @jverrydt, https://github.com/developmentseed/titiler-stacapi/pull/30)

## [0.3.0] - 2025-02-24

* Add STAC filter / sort search parameters in `/collections` endpoints (author @jverrydt, https://github.com/developmentseed/titiler-stacapi/pull/29)

## [0.2.0] - 2024-11-19

* add support for aggregations stac-api extension to fetch dynamic time information (author @jverrydt, https://github.com/developmentseed/titiler-stacapi/pull/28)

## [0.1.1] - 2024-08-20

* add support for `cube:dimensions` extension (author @jverrydt, https://github.com/developmentseed/titiler-stacapi/pull/26)
* allow overriding the colormap/expression in the  (author @jverrydt, https://github.com/developmentseed/titiler-stacapi/pull/26)

## [0.1.0] - 2024-06-11

* initial release

[Unreleased]: <https://github.com/developmentseed/titiler-stacapi/compare/2.1.0..main>
[2.1.0]: <https://github.com/developmentseed/titiler-stacapi/compare/2.0.3..2.1.0>
[2.0.3]: <https://github.com/developmentseed/titiler-stacapi/compare/2.0.2..2.0.3>
[2.0.2]: <https://github.com/developmentseed/titiler-stacapi/compare/2.0.1..2.0.2>
[2.0.1]: <https://github.com/developmentseed/titiler-stacapi/compare/2.0.0..2.0.1>
[2.0.0]: <https://github.com/developmentseed/titiler-stacapi/compare/1.1.3..2.0.0>
[1.1.3]: <https://github.com/developmentseed/titiler-stacapi/compare/1.1.2..1.1.3>
[1.1.2]: <https://github.com/developmentseed/titiler-stacapi/compare/1.1.1..1.1.2>
[1.1.1]: <https://github.com/developmentseed/titiler-stacapi/compare/1.1.0..1.1.1>
[1.1.0]: <https://github.com/developmentseed/titiler-stacapi/compare/1.0.0..1.1.0>
[1.0.0]: <https://github.com/developmentseed/titiler-stacapi/compare/0.4.0..1.0.0>
[0.4.0]: <https://github.com/developmentseed/titiler-stacapi/compare/0.3.3..0.4.0>
[0.3.3]: <https://github.com/developmentseed/titiler-stacapi/compare/0.3.2..0.3.3>
[0.3.2]: <https://github.com/developmentseed/titiler-stacapi/compare/0.3.1..0.3.2>
[0.3.1]: <https://github.com/developmentseed/titiler-stacapi/compare/0.3.0..0.3.1>
[0.3.0]: <https://github.com/developmentseed/titiler-stacapi/compare/0.2.0..0.3.0>
[0.2.0]: <https://github.com/developmentseed/titiler-stacapi/compare/0.1.1..0.2.0>
[0.1.1]: <https://github.com/developmentseed/titiler-stacapi/compare/0.1.0..0.1.1>
[0.1.0]: <https://github.com/developmentseed/titiler-stacapi/tree/0.1.0>
