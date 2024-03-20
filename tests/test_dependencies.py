"""test titiler-pgstac dependencies."""

from starlette.requests import Request

from titiler.stacapi import dependencies
from titiler.stacapi.enums import MediaType


def test_media_type():
    """test accept_media_type dependency."""
    assert (
        dependencies.accept_media_type(
            "application/json;q=0.9, text/html;q=1.0",
            [MediaType.json, MediaType.html],
        )
        == MediaType.html
    )

    assert (
        dependencies.accept_media_type(
            "application/json;q=0.9, text/html;q=0.8",
            [MediaType.json, MediaType.html],
        )
        == MediaType.json
    )

    # if no quality then default to 1.0
    assert (
        dependencies.accept_media_type(
            "application/json;q=0.9, text/html",
            [MediaType.json, MediaType.html],
        )
        == MediaType.html
    )

    # Invalid Quality
    assert (
        dependencies.accept_media_type(
            "application/json;q=w, , text/html;q=0.1",
            [MediaType.json, MediaType.html],
        )
        == MediaType.html
    )

    assert (
        dependencies.accept_media_type(
            "*",
            [MediaType.json, MediaType.html],
        )
        == MediaType.json
    )


def test_output_type():
    """test OutputType dependency."""
    req = Request(
        {
            "type": "http",
            "client": None,
            "query_string": "",
            "headers": ((b"accept", b"application/json"),),
        },
        None,
    )
    assert (
        dependencies.OutputType(
            req,
        )
        == MediaType.json
    )

    req = Request(
        {
            "type": "http",
            "client": None,
            "query_string": "",
            "headers": ((b"accept", b"text/html"),),
        },
        None,
    )
    assert (
        dependencies.OutputType(
            req,
        )
        == MediaType.html
    )

    req = Request(
        {"type": "http", "client": None, "query_string": "", "headers": ()}, None
    )
    assert not dependencies.OutputType(req)

    # FastAPI will parse the request first and inject `f=json` in the dependency
    req = Request(
        {
            "type": "http",
            "client": None,
            "query_string": "f=json",
            "headers": ((b"accept", b"text/html"),),
        },
        None,
    )
    assert dependencies.OutputType(req, f="json") == MediaType.json
