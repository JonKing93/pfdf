"""
Subpackage to export a stream segment network to geojson
----------
Main Function:
    features    - Converts a segment network to geojson

Submodules:
    _geojson    - Creates geojson FeatureCollections for various feature types
    _reproject  - Reprojects feature geometries to desired CRS
"""

from pfdf.segments._geojson._geojson import features
