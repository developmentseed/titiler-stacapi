
### STAC Collections endpoints


| Method | URL                                                                              | Output                                  | Description
| ------ | ---------------------------------------------------------------------------------|-----------------------------------------|--------------
| `GET`  | `/collections/{collection_id}/tiles/{TileMatrixSetId}/{z}/{x}/{y}[@{scale}x][.{format}]` | image/bin                               | Create a web map tile image for a collection and a tile index
| `GET`  | `/collections/{collection_id}/{TileMatrixSetId}/tilejson.json`                           | JSON ([TileJSON][tilejson_model])       | Return a Mapbox TileJSON document
| `GET`  | `/collections/{collection_id}/{TileMatrixSetId}/map`                                     | HTML                                    | simple map viewer

### Tiles

`:endpoint:/collections/{collection_id}/tiles/{TileMatrixSetId}/{z}/{x}/{y}[@{scale}x][.{format}]`

- PathParams:
    - **collection_id**: STAC Collection Identifier.
    - **TileMatrixSetId**: TileMatrixSet name (e.g `WebMercatorQuad`).
    - **z**: Tile's zoom level.
    - **x**: Tile's column.
    - **y**: Tile's row.
    - **scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
    - **format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value. OPTIONAL

- QueryParams:
    - **assets** (array[str]): asset names.
    - **expression** (str): rio-tiler's math expression with asset names (e.g `Asset1_b1/Asset2_b1`).
    - **asset_as_band** (bool): tell rio-tiler that each asset is a 1 band dataset, so expression `Asset1/Asset2` can be passed.
    - **asset_bidx** (array[str]): Per asset band index (e.g `Asset1|1;2;3`).
    - **nodata**: Overwrite internal Nodata value. OPTIONAL
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): RasterIO resampling algorithm. Defaults to `nearest`.
    - **reproject** (str): WarpKernel resampling algorithm (only used when doing re-projection). Defaults to `nearest`.
    - **algorithm** (str): Custom algorithm name (e.g `hillshade`).
    - **algorithm_params** (str): JSON encoded algorithm parameters.
    - **rescale** (array[str]): Comma (',') delimited Min,Max range (e.g `rescale=0,1000`, `rescale=0,1000&rescale=0,3000&rescale=0,2000`).
    - **color_formula** (str): rio-color formula.
    - **colormap** (str): JSON encoded custom Colormap.
    - **colormap_name** (str): rio-tiler color map name.
    - **return_mask** (bool): Add mask to the output data. Default is True.
    - **buffer** (float): Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).
    - **padding** (int): Padding to apply to each tile edge. Helps reduce resampling artefacts along edges. Defaults to `0`
    - **pixel_selection** (str): Pixel selection method (https://cogeotiff.github.io/rio-tiler/mosaic/).

- STAC API Search QueryParams:
    - **ids** (str): Comma (',') delimited list of IDS.
    - **bbox** (str): Comma (',') delimited BoundingBox (not used in the search query, but usefull to limit the bbox of the mosaic).
    - **datetime** (str): Datetime filter for the Search Query following `RFC 3339` format (https://github.com/radiantearth/stac-api-spec/blob/v1.0.0/implementation.md#datetime-parameter-handling)
    - **limit** (int): The maximum number of results to return (page size). Defaults to 10.
    - **max_items** (int): The maximum number of items to used in a mosaic. Defaults to 100.

!!! important
    **assets** OR **expression** is required

Example:

- `https://myendpoint/collections/my-collection/tiles/WebMercatorQuad/1/2/3?assets=B01`
- `https://myendpoint/collections/my-collection/tiles/WebMercatorQuad/1/2/3.jpg?assets=B01`
- `https://myendpoint/collections/my-collection/tiles/WorldCRS84Quad/1/2/3@2x.png?assets=B01&assets=B02&assets=B03`
- `https://myendpoint/collections/my-collection/tiles/WorldCRS84Quad/1/2/3?assets=B01&rescale=0,1000&colormap_name=cfastie`

### TilesJSON

`:endpoint:/collections/{collection_id}[/{TileMatrixSetId}]/tilejson.json`

- PathParams:
    - **collection_id**: STAC Collection Identifier.
    - **TileMatrixSetId**: TileMatrixSet name (e.g `WebMercatorQuad`).

- QueryParams:
    - **tile_format**: Output image format, default is set to None and will be either JPEG or PNG depending on masked value.
    - **tile_scale**: Tile size scale, default is set to 1 (256x256). OPTIONAL
    - **minzoom**: Overwrite default minzoom. OPTIONAL
    - **maxzoom**: Overwrite default maxzoom. OPTIONAL
    - **expression** (str): rio-tiler's math expression with asset names (e.g `Asset1_b1/Asset2_b1`).
    - **asset_as_band** (bool): tell rio-tiler that each asset is a 1 band dataset, so expression `Asset1/Asset2` can be passed.
    - **asset_bidx** (array[str]): Per asset band index (e.g `Asset1|1;2;3`).
    - **nodata** (str, int, float): Overwrite internal Nodata value.
    - **unscale** (bool): Apply dataset internal Scale/Offset.
    - **resampling** (str): RasterIO resampling algorithm. Defaults to `nearest`.
    - **reproject** (str): WarpKernel resampling algorithm (only used when doing re-projection). Defaults to `nearest`.
    - **algorithm** (str): Custom algorithm name (e.g `hillshade`).
    - **algorithm_params** (str): JSON encoded algorithm parameters.
    - **rescale** (array[str]): Comma (',') delimited Min,Max range (e.g `rescale=0,1000`, `rescale=0,1000&rescale=0,3000&rescale=0,2000`).
    - **color_formula** (str): rio-color formula.
    - **colormap** (str): JSON encoded custom Colormap.
    - **colormap_name** (str): rio-tiler color map name.
    - **return_mask** (bool): Add mask to the output data. Default is True.
    - **buffer** (float): Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).
    - **padding** (int): Padding to apply to each tile edge. Helps reduce resampling artefacts along edges. Defaults to `0`
    - **pixel_selection** (str): Pixel selection method (https://cogeotiff.github.io/rio-tiler/mosaic/).

- STAC API Search QueryParams:
    - **ids** (str): Comma (',') delimited list of IDS.
    - **bbox** (str): Comma (',') delimited BoundingBox (not used in the search query, but usefull to limit the bbox of the mosaic).
    - **datetime** (str): Datetime filter for the Search Query following `RFC 3339` format (https://github.com/radiantearth/stac-api-spec/blob/v1.0.0/implementation.md#datetime-parameter-handling)
    - **limit** (int): The maximum number of results to return (page size). Defaults to 10.
    - **max_items** (int): The maximum number of items to used in a mosaic. Defaults to 100.

!!! important
    **assets** OR **expression** is required

Example:

- `https://myendpoint/collections/my-collection/WebMercatorQuad/tilejson.json?assets=B01`
- `https://myendpoint/collections/my-collection/WebMercatorQuad/tilejson.json?assets=B01&tile_format=png`
- `https://myendpoint/collections/my-collection/WorldCRS84Quad/tilejson.json?assets=B01&tile_scale=2`

[tilejson_model]: https://github.com/developmentseed/titiler/blob/2335048a407f17127099cbbc6c14e1328852d619/src/titiler/core/titiler/core/models/mapbox.py#L16-L38
