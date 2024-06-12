"""titiler.stacapi ogcapi pydantic models.

This might be moved in an external python module

see: https://github.com/developmentseed/ogcapi-pydantic

"""

from typing import Dict, List, Optional, TypedDict, Union

from geojson_pydantic import Feature, Point
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from titiler.stacapi.enums import MediaType


class Link(BaseModel):
    """Link model.

    Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/common-core/link.yaml

    Code generated using https://github.com/koxudaxi/datamodel-code-generator/
    """

    href: Annotated[
        str,
        Field(
            description="Supplies the URI to a remote resource (or resource fragment).",
            json_schema_extra={"example": "http://data.example.com/buildings/123"},
        ),
    ]
    rel: Annotated[
        str,
        Field(
            description="The type or semantics of the relation.", example="alternate"
        ),
    ]
    type: Annotated[
        Optional[MediaType],
        Field(
            description="A hint indicating what the media type of the result of dereferencing the link should be.",
            json_schema_extra={
                "example": "application/geo+json",
            },
        ),
    ] = None
    templated: Annotated[
        Optional[bool],
        Field(description="This flag set to true if the link is a URL template."),
    ] = None
    varBase: Annotated[
        Optional[str],
        Field(
            description="A base path to retrieve semantic information about the variables used in URL template.",
            json_schema_extra={
                "example": "/ogcapi/vars/",
            },
        ),
    ] = None
    hreflang: Annotated[
        Optional[str],
        Field(
            description="A hint indicating what the language of the result of dereferencing the link should be.",
            json_schema_extra={
                "example": "en",
            },
        ),
    ] = None
    title: Annotated[
        Optional[str],
        Field(
            description="Used to label the destination of a link such that it can be used as a human-readable identifier.",
            json_schema_extra={
                "example": "Trierer Strasse 70, 53115 Bonn",
            },
        ),
    ] = None
    length: Optional[int] = None

    model_config = {"use_enum_values": True}


class Landing(BaseModel):
    """Landing page model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/landingPage.yaml

    """

    title: Optional[str] = None
    description: Optional[str] = None
    links: List[Link]


class Properties(BaseModel):
    """Model for FeatureInfo properties."""

    values: List[Union[float, int]]
    I: int  # noqa: E741
    J: int  # noqa: E741
    dimension: Dict[str, str]
    tileMatrixSet: str
    tileMatrix: int
    tileRow: int
    tileCol: int


FeatureInfo = Feature[Point, Properties]


class LayerDict(TypedDict, total=False):
    """Layer."""

    id: str
    collection: str
    bbox: List[float]
    format: Optional[str]
    style: str
    render: Optional[Dict]
    tilematrixsets: Dict
    time: Optional[List[str]]
    query_string: str
