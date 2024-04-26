"""test get_dependency_params."""

from titiler.core.dependencies import RescalingParams
from titiler.stacapi.factory import get_dependency_params


def test_get_params_rescale():
    """test get_dependency_params for rescale."""

    def _parse_rescale(rescale):
        rescales = []
        for r in qs["rescale"]:
            if not isinstance(r, str):
                rescales.append(",".join(map(str, r)))
            else:
                rescales.append(r)

        return rescales

    qs = {"rescale": ["0,1", "2,3"]}
    assert get_dependency_params(
        dependency=RescalingParams,
        query_params={"rescale": _parse_rescale(qs)},
    ) == [(0.0, 1.0), (2.0, 3.0)]

    qs = {"rescale": [[0, 1], [2, 3]]}
    assert get_dependency_params(
        dependency=RescalingParams,
        query_params={"rescale": _parse_rescale(qs)},
    ) == [(0.0, 1.0), (2.0, 3.0)]
