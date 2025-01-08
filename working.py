import fiona
from pfdf.projection import CRS

schema = {
    "geometry": "MultiPoint",
    "properties": {'value': 'int'},
}
crs = CRS(26911)

record1 = {
    "properties": {'value': 1},
    "geometry": {"type": "MultiPoint", "coordinates": [[1, 2], [3, 4], [5, 6]]},
}
record2 = {
    "properties": {'value': 2},
    "geometry": {"type": "MultiPoint", "coordinates": [[10, 12], [14, 16], [18, 20]]},
}

with fiona.open("test.geojson", "w", driver="GeoJSON", schema=schema, crs=crs) as file:
    file.write(record1)
    file.write(record2)



from pfdf.raster import Raster
r1 = Raster.from_points('test.geojson', resolution=1, field='value', nodata=0)
r2 = Raster.from_points('test.geojson', resolution=1, field='value', nodata=0, bounds=[0, 0, 17, 18, 26911])

