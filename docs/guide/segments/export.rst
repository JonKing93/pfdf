Export
======

It's often useful to export segments and assessment results to other formats for visualization, and the class provides two methods to support this. The :ref:`save <pfdf.segments.Segments.save>` method saves a network to a vector feature file, and the :ref:`geojson <pfdf.segments.Segments.geojson>` method converts a network to a `geojson.FeatureCollection <https://pypi.org/project/geojson/#featurecollection>`_.

.. note:: The examples on this page are for ShapeFiles, but pfdf supports most common vector file formats. See the :ref:`vector driver guide <vector-drivers>` for more information on supported formats. 

Export Types
------------
Both methods support 4 types of export:

.. _export-types:

.. list-table::
    :header-rows: 1

    * - Type
      - Description
    * - segments
      - Stream segments as LineString geometries
    * - basins
      - Terminal outlet basins as Polygon geometries
    * - outlets
      - Terminal outlets as Point geometries
    * - segment outlets
      - All outlets as Point geometries

By default, both methods will export segments, but you can use the "type" option to select a different type::

    # Save segments as LineStrings (default)
    segments.save('segments.shp')

    # Save basins and outlets (Polygons and Points)
    segments.save('basins.shp', type="basins")
    segments.save('outlets.shp', "outlets")
    segments.save('all-outlets.shp', "segment outlets")


Properties
----------

Both methods allow an optional ``properties`` input, which can be used to tag the features with associated data values. The properties input should be a ``dict`` whose keys are the names of data fields (as strings), and whose values are 1D numpy arrays with one element per exported feature. Each array should have an integer, floating-point, boolean, or string dtype. There are no required data fields, so you may use any data field names supported by geojson. However, note that data field names may be truncated when saving to certain vector file formats (for example, saving to a Shapefile will truncate field names to 10 characters)::

    # Export segments and include data properties
    properties = {
        "id": segments.ids,
        "hazard": my_assessment_results,
        "catchment_area": segments.area(),
        "legend": ["Low hazard", "Moderate hazard", ...],
    }
    segments.save('segments.shp', "segments", properties)

If you are exporting basins or outlets, then the property arrays may optionally have one element per local drainage network, as opposed to one element per segment. Either case is allowed, and the terminal outlet values will be extracted as needed.

::

    # Export basins and include data properties
    basins = segments.isterminus
    properties = {
        "id": segments.terminal_ids,     # One element per terminal segment 
        "hazard": my_assessment_results, # One element per segment
    }
    segments.save('basins.shp', "basins", properties)


CRS
---
By default, both methods will export the features using the :ref:`CRS <guide-crs>` of the flow-direction raster used to derive the network. However, you can use the ``crs`` option to export the features to a different CRS instead:

.. code:: pycon

  >>> # Default would export to EPSG:26911
  >>> segments.crs.to_epsg()
  26911

  >>> # But this will export to EPSG:4326 instead
  >>> segments.save('segments.shp', crs=4326)




__geo_interface__
-----------------

The class also supports the `__geo_interface__ <https://gist.github.com/sgillies/2217756>`_ protocol::

    geojson_dict = segments.__geo_interface__

This returns a dict-like ``geojson.FeatureCollection``, and is equivalent to calling the ``geojson`` method for segments with no properties::

  # Same output
  geojson_dict = segments.__geo_interface__
  the_same_dict = segments.geojson(type="segments", properties=None)
