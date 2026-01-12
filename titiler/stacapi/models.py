"""titiler.stacapi ogcapi pydantic models.

This might be moved in an external python module

see: https://github.com/developmentseed/ogcapi-pydantic

"""

from typing import TypedDict, Union

from geojson_pydantic import Feature, Point
from pydantic import BaseModel

from titiler.core.utils import TMSLimits


class Properties(BaseModel):
    """Model for FeatureInfo properties."""

    values: list[Union[float, int]]
    I: int  # noqa: E741
    J: int  # noqa: E741
    dimension: dict[str, str]
    tileMatrixSet: str
    tileMatrix: int
    tileRow: int
    tileCol: int


FeatureInfo = Feature[Point, Properties]


class LayerDict(TypedDict, total=False):
    """Layer."""

    id: str
    collection: str
    title: str | None
    bbox: list[float]
    format: str | None
    style: str
    render: dict | None
    tilematrixsets: dict[str, list[TMSLimits]]
    time: list[str] | None
    query_string: str
