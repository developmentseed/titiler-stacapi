

## [Unreleased]

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

[Unreleased]: <https://github.com/developmentseed/titiler-stacapi/compare/0.4.0..main>
[0.4.0]: <https://github.com/developmentseed/titiler-stacapi/compare/0.3.3..0.4.0>
[0.3.3]: <https://github.com/developmentseed/titiler-stacapi/compare/0.3.2..0.3.3>
[0.3.2]: <https://github.com/developmentseed/titiler-stacapi/compare/0.3.1..0.3.2>
[0.3.1]: <https://github.com/developmentseed/titiler-stacapi/compare/0.3.0..0.3.1>
[0.3.0]: <https://github.com/developmentseed/titiler-stacapi/compare/0.2.0..0.3.0>
[0.2.0]: <https://github.com/developmentseed/titiler-stacapi/compare/0.1.1..0.2.0>
[0.1.1]: <https://github.com/developmentseed/titiler-stacapi/compare/0.1.0..0.1.1>
[0.1.0]: <https://github.com/developmentseed/titiler-stacapi/tree/0.1.0>
