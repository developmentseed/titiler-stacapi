"""titiler.stacapi utilities.

Code from titiler.pgstac and titiler.cmr, MIT License.

"""

import re
import time
from typing import Any, Optional, Sequence, Type, Union

import orjson
from starlette.requests import Request
from starlette.templating import Jinja2Templates, _TemplateResponse


def retry(
    tries: int,
    exceptions: Union[Type[Exception], Sequence[Type[Exception]]] = Exception,
    delay: float = 0.0,
):
    """Retry Decorator"""

    def _decorator(func: Any):
        def _newfn(*args: Any, **kwargs: Any):

            attempt = 0
            while attempt < tries:
                try:
                    return func(*args, **kwargs)

                except exceptions:  # type: ignore

                    attempt += 1
                    time.sleep(delay)

            return func(*args, **kwargs)

        return _newfn

    return _decorator


def create_html_response(
    request: Request,
    data: str,
    templates: Jinja2Templates,
    template_name: str,
    router_prefix: Optional[str] = None,
) -> _TemplateResponse:
    """Create Template response."""
    urlpath = request.url.path
    if root_path := request.app.root_path:
        urlpath = re.sub(r"^" + root_path, "", urlpath)

    crumbs = []
    baseurl = str(request.base_url).rstrip("/")

    crumbpath = str(baseurl)
    for crumb in urlpath.split("/"):
        crumbpath = crumbpath.rstrip("/")

        part = crumb
        if part is None or part == "":
            part = "Home"

        crumbpath += f"/{crumb}"
        crumbs.append({"url": crumbpath.rstrip("/"), "part": part.capitalize()})

    if router_prefix:
        baseurl += router_prefix

    return templates.TemplateResponse(
        f"{template_name}.html",
        {
            "request": request,
            "response": orjson.loads(data),
            "template": {
                "api_root": baseurl,
                "params": request.query_params,
                "title": "",
            },
            "crumbs": crumbs,
            "url": str(request.url),
            "baseurl": baseurl,
            "urlpath": str(request.url.path),
            "urlparams": str(request.url.query),
        },
    )
