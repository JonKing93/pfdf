import arcpy

extent_code_field_name = "Extent_Code"


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

def extent(perimeter, bounds, buffered, buffer, raster, cellsize)
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
    arcpy.analysis.Buffer(bounds, extentbox, buffer)

    # Export to raster
    arcpy.conversion.PolygonToRaster(extentbox, 'OBJECTID', raster, 'CELL_CENTER', cellsize=cellsize)

def demtiles(extent, dem, projected, intersect, firedem)
    """
    calculate.demtiles  Return the list of DEM tiles that contain the fire area
    ----------
    tiles = calculate.demtiles(extent, dem, projected, intersect, firedem)
    Determines the DEM tiles that contain the fire area and returns the File IDs
    of those tiles as a list. Begins by projecting the fire extent box into the
    same projection as the DEM tiles index. Then, groups the DEM tiles that
    intersect the extent box into a layer, and exports the layer to a new
    feature. Returns the file IDs of the tiles in this feature as a list.
    ----------
    Inputs:
        extent (str): The path to the input arcpy feature holding the extent box
            of the fire perimeter
        dem (str): The path to the input arcpy feature holding the polygon tiles
            of the DEM
        projected (str): The path to the output arcpy feature holding the extent
            box projected into the same system as the DEM
        intersect (str): The path to the output arcpy layer selecting the DEM
            tiles that overlap with the extent box
        firedem (str): The path to the output arcpy feature holding the DEM
            tiles that contain the fire extent box

    Outputs:
        tiles (str list): A list of File IDs for the DEM tiles that contain the
            fire area.

    Saves:
        Files matching the names of the projected, intersect, and firedem inputs
    """

    # Project the extent box into the projection used by the DEM
    projection = arcpy.Describe(dem).spatialReference
    arcpy.management.Project(extent, projected, projection)
    extent = projected

    # Get the DEM tiles that include the extent box
    arcpy.management.MakeFeatureLayer(dem, intersect)
    arcpy.management.SelectLayerByLocation(intersect, "INTERSECT", extent)
    arcpy.management.CopyFeatures(intersect, firedem)

    # Return the files with the DEM data needed to model the fire area
    demfiles = arcpy.da.TableToNumPyArray(firedem, 'FILE_ID')
    demfiles = demfiles['FILE_ID'].tolist()
    return demfiles

def mosaic(tiles, mosaic):
    """
    calculate.mosaic  Creates a mosaic of raster datasets
    """

    for t in range(0, len(tiles)):
        if t==0:
            arcpy.management.Copy(tiles[t], mosaic)
        else:
            arcpy.management.Copy(tiles[t], mosaic)












