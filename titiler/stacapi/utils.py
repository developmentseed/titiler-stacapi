"""titiler.stacapi utilities.

Code from titiler.pgstac and titiler.cmr, MIT License.

"""

import re
import time
from typing import Any, List, Optional

from morecantile import TileMatrixSet
from starlette.requests import Request
from starlette.templating import Jinja2Templates, _TemplateResponse


def create_html_response(
    request: Request,
    data: Any,
    templates: Jinja2Templates,
    template_name: str,
    title: Optional[str] = None,
    router_prefix: Optional[str] = None,
    **kwargs: Any,
) -> _TemplateResponse:
    """Create Template response."""
    urlpath = request.url.path
    if root_path := request.app.root_path:
        urlpath = re.sub(r"^" + root_path, "", urlpath)

    if router_prefix:
        urlpath = re.sub(r"^" + router_prefix, "", urlpath)

    crumbs = []
    baseurl = str(request.base_url).rstrip("/")

    if router_prefix:
        baseurl += router_prefix

    crumbpath = str(baseurl)
    if urlpath == "/":
        urlpath = ""

    for crumb in urlpath.split("/"):
        crumbpath = crumbpath.rstrip("/")
        part = crumb
        if part is None or part == "":
            part = "Home"
        crumbpath += f"/{crumb}"
        crumbs.append({"url": crumbpath.rstrip("/"), "part": part.capitalize()})

    return templates.TemplateResponse(
        request,
        name=f"{template_name}.html",
        context={
            "response": data,
            "template": {
                "api_root": baseurl,
                "params": request.query_params,
                "title": title or template_name,
            },
            "crumbs": crumbs,
            "url": baseurl + urlpath,
            "params": str(request.url.query),
            **kwargs,
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


def _tms_limits(
    tms: TileMatrixSet,
    bounds: List[float],
    zooms: Optional[List[int]] = None,
) -> List:
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
