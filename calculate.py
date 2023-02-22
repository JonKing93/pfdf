import arcpy
import os.path
import notify.regrid


def utmzone(perimeter, utm, dissolved, centroid, centroid_utm, zone):
    """
    calculate.utmzone  Returns the UTM zone of the centroid of the fire perimeter
    ----------
    zone = calculate.utmzone(perimeter, utm, dissolved, centroid, centroid_utm, zone)
    Returns the UTM zone for a fire perimeter. Dissolves all perimeter into a
    single (possibly multi-part) polygon and determines the centroid of that
    polygon. Projects the centroid to UTM and determines its UTM zone using the
    overlap of the centroid with UTM zone polygons. Returns the UTM zone as an
    int.
    ----------
    Inputs:
        perimeter (str): The path to the input arcpy feature holding the fire
            perimeter polygons
        utm (str): The path to the input arcpy feature holding the UTM zone
            polygons. The polygons must include a "ZONE" field.
        dissolved (str): The path to the output arcpy feature holding the
            dissolved (merged) fire perimeter polygon.
        centroid (str): The path to the output arcpy feature holding the
            centroid of the fire perimeter
        centroid_utm (str): The path to the output arcpy feature holding the
            centroid of the fire perimeter projected to UTM.
        zone (str): The path to the output arcpy feature identifying the UTM
            zone of the centroid of the fire perimeter.

    Outputs:
        zone (int): The UTM zone of the centroid of the fire perimeter

    Saves:
        Files matching names of the dissolved, centroid, and zone inputs.
    """

    # Dissolve (merge) polygons into a single fire-perimeter polygon. Get the
    # centroid of this polygon
    arcpy.management.Dissolve(perimeter, dissolved)
    arcpy.management.FeatureToPoint(dissolved, centroid)

    # Project the centroid into the same ... as the UTM polygons. Then determine
    # the UTM zone polygon that contains the centroid.
    arcpy.management.Project(centroid, centroid_utm, utm)
    arcpy.analysis.Identity(centroid, utm, zone)

    # Return zone as an int
    zones = arcpy.da.TableToNumPyArray(zone, "ZONE")
    zone = zones["ZONE"][0]
    return int(zone)

def extent(perimeter, bounds, buffered, buffer, raster, cellsize):
    """
    calculate.extent  Returns an extent box for the fire perimeter as a raster.
    ----------
    calculate.extent(perimeter, bounds, buffered, buffer, raster, cellsize)
    Finds a rectangular bounding box of minimum area that surrounds the fire
    perimeters. Adds a buffer so the fire perimeter is not on the very edge of
    the extent box, then converts the box to a raster.
    ----------
    Inputs:
        perimeter (str): The path to the input arcpy feature holding the fire perimeter
        bounds (str): The path to the output arcpy feature holding the minimum
            bounding box for the fire perimeter.
        buffered (str): The path to the output arcpy feature holding the
            buffered bounding box
        buffer (positive float): The size of the buffer to apply to the extent box.
        raster (str): The path to the output arcpy raster for the extent box.
        cellsize (float): The resolution (in meters) to use when converting the
            extent box to a raster.

    Saves:
        Files matching the names of the bounds, buffered, and raster inputs.
    """

    # Get a rectangular bounding box (extent box) that contains the fire
    # perimeter. Buffer the edges so the perimeter is not on the very edge.
    arcpy.management.MinimumBoundingGeometry(perimeter, bounds, 'RECTANGLE_BY_AREA')
    arcpy.analysis.Buffer(bounds, buffered, buffer)

    # Export to raster
    arcpy.conversion.PolygonToRaster(buffered, 'OBJECTID', raster, 'CELL_CENTER', cellsize=cellsize)

def firetiles(extent, demtiles, projected, intersect, firetiles):
    """
    calculate.firetiles  Return the list of DEM tiles that contain the fire area
    ----------
    tiles = calculate.firetiles(extent, demtiles, projected, intersect, firetiles)
    Determines the DEM tiles that contain the fire area and returns the File IDs
    of those tiles as a list. Begins by projecting the fire extent box into the
    same projection as the DEM tiles index. Then, groups the DEM tiles that
    intersect the extent box into a layer, and exports the layer to a new
    feature. Returns the file IDs of the tiles in this feature as a list.
    ----------
    Inputs:
        extent (str): The path to the input arcpy feature holding the extent box
            of the fire perimeter
        demtiles (str): The path to the input arcpy feature holding the polygon tiles
            of the DEM
        projected (str): The path to the output arcpy feature holding the extent
            box projected into the same system as the DEM
        intersect (str): The path to the output arcpy layer selecting the DEM
            tiles that overlap with the extent box
        firetiles (str): The path to the output arcpy feature holding the DEM
            tiles that contain the fire extent box

    Outputs:
        tiles (str list): A list of File IDs for the DEM tiles that contain the
            fire area.

    Saves:
        Files matching the names of the projected, intersect, and firedem inputs
    """

    # Project the extent box into the projection used by the DEM
    projection = arcpy.Describe(demtiles).spatialReference
    arcpy.management.Project(extent, projected, projection)
    extent = projected

    # Get the DEM tiles that include the extent box
    arcpy.management.MakeFeatureLayer(demtiles, intersect)
    arcpy.management.SelectLayerByLocation(intersect, "INTERSECT", extent)
    arcpy.management.CopyFeatures(intersect, firetiles)

    # Return the files with the DEM data needed to model the fire area
    demfiles = arcpy.da.TableToNumPyArray(firetiles, 'FILE_ID')
    demfiles = demfiles['FILE_ID'].tolist()
    return demfiles

def mosaic(rasters, mosaic):
    """
    calculate.mosaic  Creates a mosaic of raster datasets
    ----------
    calculate.mosaic(rasters, mosaic)
    Merges a set of rasters into a single raster (also known as a mosaic).
    Creates a new arcpy raster holding the final mosaic.
    ----------
    Inputs:
        rasters (str list): A list of paths to the input rasters that should be 
            merged into a mosaic.
        mosaic (str): The path to the output raster mosaic

    Saves:
        A file matching the name of the mosaic input.
    """

    # Initialize the mosaic
    [path, name] = os.path.split(mosaic)
    arcpy.management.CreateRasterDataset(path, name)

    # Add each raster
    for raster in rasters:
        arcpy.management.Mosaic(raster, mosaic)

def clip(extent, basins, projected, clipped):
    """
    calculate.clip  Clip a set of basin features to the fire extent box
    ----------
    calculate.clip(extent, basins, projected, clipped)
    Reduces a set of debris-basin feature to the features within the fire
    perimeter extent box. Projects the debris-basin features into the same
    system as the extent box before clipping. The output clipped features will
    be in the same projection as the input extent box.
    ----------
    Inputs:
        extent (str): The path to the input arcpy feature holding the fire
            perimeter extent box
        basins (str): The path to the input arcpy features holding the 
            debris-basins to be clipped
        projected (str): The path to the output arcpy feature holding the 
            debris-basins projected into the same system as the extent box
        clipped (str): The path to the output arcpy feature holding the
            debris-basins 

    Saves:
        Files matching the names of the projected and clipped inputs
    """

    # Project the basins into the same system as the extent box
    projection = arcpy.Describe(extent).spatialReference
    arcpy.management.Project(basins, projected, projection)

    # Clip the basins to the fire perimeter extent box
    arcpy.analysis.Clip(projected, extent, clipped)

def rasterSize(raster):
    """
    calculate.rasterSize  Return the size of a raster dataset.
    ----------
    size = calculate.rasterSize(raster)
    Returns the size of a raster dataset. The output size is a list with two
    elements - the first element is the number of rows, and the second is the
    number of columns. If the raster dataset does not exist, throws an error.

    size = calculate.rasterSize(raster, required=False)
    Indicate that the raster dataset is not required to exist. If the raster
    does not exist, returns None instead of a size list.
    ----------
    Inputs:
        raster (str): The path to an input arcpy raster dataset
        required (bool): True (default) if the function should throw an error
            when the raster does not exist. Set to False to return a size of 
            [0, 0] instead.

    Outputs:
        size (int list [2] | None): The size of the queried raster. First
            element is the number of rows, second is the number of columns. If
            the raster does not exist and is not required, returns None.
    """

    # Handle non-existent rasters
    if not arcpy.Exists(raster):
        if required:
            raise ValueError(f'The raster does not exist\n\tRaster: {raster}')
        else:
            return None

    # Get the size
    nRows = arcpy.management.GetRasterProperties(raster, 'ROWCOUNT')
    nCols = arcpy.management.GetRasterProperties(raster, 'COLUMNCOUNT')
    return [nRows, nCols]

def regrid(raster, extent, regridded):
    """
    calculate.regrid  Regrids a raster dataset to the fire extent box
    ----------
    regridded = calculate.regrid(raster, extent, regridded)
    Restricts an input raster dataset to the domain of an input raster extent.
    Saves the regridded raster to a new arcpy raster. Returns the path to this
    raster.
    ----------
    Inputs:
        raster (str): The path to the input arcpy raster that should be regridded
        extent (arcpy Raster): The raster object for the fire extent
        regridded (str): The path to the output arcpy raster holding the
            regridded dataset.

    Outputs:
        regridded (str): The path to the output arcpy raster holding the
            regridded dataset.
    """

    # Apply the extent raster to the input dataset and save
    dataset = Raster(raster)
    dataset = extent * dataset
    dataset.save(regridded)

    # Return the path to the regridded raster
    return regridded










