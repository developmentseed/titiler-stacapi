
### OGC WMTS endpoints


| Method | URL                                                                                        | Output                       | Description
| ------ | -------------------------------------------------------------------------------------------|------------------------------|--------------
| `GET`  | `/wmts`                                                                                    | XML or image/bin or GeoJSON  | OGC Web map tile service (KVP encoding)
| `GET`  | `/layers/{LAYER}/{STYLE}/{TIME}/{TileMatrixSet}/{TileMatrix}/{TileCol}/{TileRow}.{FORMAT}` | image/bin                    | OGC GetTile (REST encoding)

### WMTS (GetCapabilities / GetTile / GetFeatureInfo) - KVP Encoding

`:endpoint:/wmts`

- QueryParams:

    - `GetCapabilities`:

        - **Request** ([`GetCapabilities`, `GetTile`, `GetFeatureInfo`]): Operation name
        - **Service** ([`wmts`]): Service type identifier
        - **Version** ([`1.0.0`], optional): Standard and schema version

    - `GetTile`:

        - **Layer** (str): Layer identifier
        - **Format** (str): Output image format
        - **Style** (str): Style identifier
        - **TileMatrixSet** (str): TileMatrixSet identifier
        - **TileMatrix** (int): TileMatrix identifier
        - **TileRow** (int): Row index of tile matrix
        - **TileCol** (int): Column index of tile matrix
        - **Time** (str, Optional): TIME Dimension

    - `GetFeatureInfo`:

        - **I** (int): Column index of a pixel in the tile
        - **J** (int): Row index of a pixel in the tile
        - **InfoFormat** ([`application/geo+json`]): Output format of the retrieved information

Example:

- `https://myendpoint/wmts?Request=GetCapabilities&Services=wmts&Version=1.0.0`
- `https://myendpoint/wmts?Request=GetTiles&Services=wmts&Version=1.0.0&Style=default&Layer=MyLayer&TileMatrixSet=WebMercatorQuad&TileMatrix=0&TileRow=0&TileCol=0&Time=2023-01-01&Format=image/png`
- `https://myendpoint/wmts?Request=GetTiles&Services=wmts&Version=1.0.0&Style=default&Layer=MyLayer&TileMatrixSet=WebMercatorQuad&TileMatrix=0&TileRow=0&TileCol=0&Time=2023-01-01&Format=image/png&I=100&J=100&InfoFormat="application/geo+json`


### GetTile - REST

`:endpoint:/layers/{LAYER}/{STYLE}/{TIME}/{TileMatrixSet}/{TileMatrix}/{TileCol}/{TileRow}.{FORMAT}`

- PathParams:
    - **Layer** (str): Layer identifier (collection_id)
    - **Style** (str): Style identifier
    - **Time** (str): TIME Dimension
    - **TileMatrixSet** (str): TileMatrixSet identifier
    - **TileMatrix** (int): TileMatrix identifier
    - **TileRow** (int): Row index of tile matrix
    - **TileCol** (int): Column index of tile matrix
    - **Format** (str): Output image format

Example:

- `https://myendpoint/layers/my-collection/default/2023-01-01/WebMercatorQuad/0/0/0.png`
