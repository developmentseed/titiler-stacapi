"""titiler.pgstac errors."""

from starlette import status

from titiler.core.errors import TilerError


class MosaicNotFoundError(TilerError):
    """Mosaic not found in PgSTAC Database."""


STACAPI_STATUS_CODES = {
    MosaicNotFoundError: status.HTTP_404_NOT_FOUND,
}
