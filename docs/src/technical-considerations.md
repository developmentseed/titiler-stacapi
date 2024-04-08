# Technical Considerations

## Optimizing Tile Requests in titiler-stacapi

To enhance the efficiency of tile requests in titiler-stacapi, it's essential to set appropriate zoom levels and bounding boxes and be mindful of the number of requests made to the STAC API. This guide will walk you through understanding and applying these settings to improve performance and avoid overloading the service with expansive queries.

### Understanding Zoom Levels

Zoom levels dictate the level of detail in the tiles requested. Specifying a range (min/max) can significantly optimize request times and resource usage.

### Bounding Box Considerations

The bounding box limits the geographical area of interest, preventing unnecessarily broad tile generation. Define this based on your application's specific needs to reduce load times and server strain.

### Mindful Usage of STAC API Requests

Each tile request to titiler-stacapi results in one request to a STAC API **`/search`**. It's vital to use this feature respectfully towards STAC API providers by being aware of the request load. High volumes of tile requests translate to an equal number of STAC API requests, which could overwhelm the API endpoints.

For detailed examples and more on optimizing your usage of titiler-stacapi, refer to the project's primary documentation.