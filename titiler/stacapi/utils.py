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


# This code is copied from marblecutter
#  https://github.com/mojodna/marblecutter/blob/master/marblecutter/stats.py
# License:
# Original work Copyright 2016 Stamen Design
# Modified work Copyright 2016-2017 Seth Fitzsimmons
# Modified work Copyright 2016 American Red Cross
# Modified work Copyright 2016-2017 Humanitarian OpenStreetMap Team
# Modified work Copyright 2017 Mapzen
class Timer(object):
    """Time a code block."""

    def __enter__(self):
        """Starts timer."""
        self.start = time.time()
        return self

    def __exit__(self, ty, val, tb):
        """Stops timer."""
        self.end = time.time()
        self.elapsed = self.end - self.start

    @property
    def from_start(self):
        """Return time elapsed from start."""
        return time.time() - self.start
