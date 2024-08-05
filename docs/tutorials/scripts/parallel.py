from pfdf import watershed
from pfdf.raster import Raster
from pfdf.segments import Segments

if __name__ == "__main__":
    # Watershed analysis
    dem = Raster("dem.tif")
    conditioned = watershed.condition(dem)
    flow = watershed.flow(conditioned)
    npixels = watershed.accumulation(flow)

    # Delineate a network
    large_enough = npixels > 250
    segments = Segments(flow, mask=large_enough)

    # Filtering
    pass

    # Hazard assessment models
    pass

    # Locate basins in parallel
    segments.locate_basins(parallel=True)

    # Save to file
    segments.save("parallel-basins.geojson", type="basins")
