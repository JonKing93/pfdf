#####
# Loading everything
#####

# Initialize the bounds
bounds = _bounds.unbounded(crs)

# Validate each feature's geometry and convert to coordinate array
geometry_values = []
for f, feature in enumerate(ffile.file):
    geometry = feature['geometry']
    multicoordinates = _validate.geometry(f, geometry, geometries)

    # Iterate through coordinates and add to feature array
    for c, coordinates in enumerate(multicoordinates):
        shape = validate_coordinates(f, c, coordinates)
        