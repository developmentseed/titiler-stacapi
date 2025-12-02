"""titiler.stacapi utilities.

Code from titiler.pgstac and titiler.cmr, MIT License.

"""

from morecantile import TileMatrixSet


def _tms_limits(
    tms: TileMatrixSet,
    bounds: list[float],
    zooms: list[int] | None = None,
) -> list:
    if zooms:
        minzoom, maxzoom = zooms
    else:
        minzoom, maxzoom = tms.minzoom, tms.maxzoom

    tilematrix_limit = []
    for zoom in range(minzoom, maxzoom + 1):
        matrix = tms.matrix(zoom)
        ulTile = tms.tile(bounds[0], bounds[3], zoom)
        lrTile = tms.tile(bounds[2], bounds[1], zoom)
        minx, maxx = (min(ulTile.x, lrTile.x), max(ulTile.x, lrTile.x))
        miny, maxy = (min(ulTile.y, lrTile.y), max(ulTile.y, lrTile.y))
        tilematrix_limit.append(
            {
                "tileMatrix": matrix.id,
                "minTileRow": max(miny, 0),
                "maxTileRow": min(maxy, matrix.matrixHeight),
                "minTileCol": max(minx, 0),
                "maxTileCol": min(maxx, matrix.matrixWidth),
            }
        )

    return tilematrix_limit
