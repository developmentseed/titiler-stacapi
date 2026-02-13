"""compat tools for titiler 2.0"""

from rio_tiler.utils import cast_to_sequence


# NOTE: This is the same as titiler.extensions.render._adapt_render_for_v2
def _adapt_render_for_v2(render: dict) -> None:
    """adapt render dict from titiler 1.0 to 2.0."""
    if assets := render.get("assets"):
        assets_with_options: dict[str, list] = {
            asset: [] for asset in cast_to_sequence(assets)
        }

        # adapt for titiler V2
        if asset_bidx := render.pop("asset_bidx", None):
            asset_bidx = cast_to_sequence(asset_bidx)
            for v in asset_bidx:
                asset, bidx = v.split("|")
                if asset in assets_with_options:
                    assets_with_options[asset].append(f"indexes={bidx}")

        # asset_expression
        if asset_expr := render.pop("asset_expression", None):
            asset_expr = cast_to_sequence(asset_expr)
            for v in asset_expr:
                asset, expr = v.split("|")
                if asset in assets_with_options:
                    assets_with_options[asset].append(f"expression={expr}")

        new_assets = []
        for asset, options in assets_with_options.items():
            if options:
                asset = asset + "|" + "&".join(options)
            new_assets.append(asset)

        render["assets"] = new_assets
