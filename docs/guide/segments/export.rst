Export
======

It's often useful to export segments and assessment results to other formats for visualization, and the class provides two methods to support this. The :ref:`save <pfdf.segments.Segments.save>` method saves a network to a vector feature file, and the :ref:`geojson <pfdf.segments.Segments.geojson>` method converts a network to a ``geojson.FeatureCollection``.

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
    >>> segments.save('segments.shp')

    # Save basins and outlets
    >>> segments.save('basins.shp', type="basins")
    >>> segments.save('outlets.shp', type="outlets")
    >>> segments.save('all-outlets.shp', type="segment outlets")


Properties
----------

Both methods allow an optional ``properties`` input, which can be used to tag the features with associated data values. The properties input should be a ``dict`` whose keys are the names of data fields (as strings), and whose values are 1D numpy arrays with one element per exported feature. Currently, the class supports numeric, real-valued properties, so the array dtypes should be integer, floating-point, or boolean. There are no required data fields, so you may use any data field names supported by geojson. However, note that data field names may be truncated when saving to certain vector file formats (for example, saving to a Shapefile will truncate field names to 10 characters)::

    properties = {
        "id": segments.ids,
        "hazard": my_assessment_results,
        "catchment_area": segments.area(),
        "my cool data field": ...
    }
    segments.save('segments.shp', properties)

Note that when exporting basins or outlets, the property values should have one element per local drainage network, rather than one element per segment. The ``isterminus`` property is often useful for this::

    basins = segments.isterminus
    properties = {
        "id": segments.ids[basins],
        "hazard": my_assessment_results[basins],
        "catchment_area": segments.area()[basins],
        "my cool data field":
    }
    segments.save('segments.shp', properties, type="basins")


__geo_interface__
-----------------

The class also supports the `__geo_interface__ <https://gist.github.com/sgillies/2217756>`_ protocol::

    >>> geojson_dict = segments.__geo_interface__

This returns a dict-like ``geojson.FeatureCollection``, and is equivalent to calling the ``geojson`` method for segments with no properties::

  # Same output
  >>> geojson_dict = segments.__geo_interface__
  >>> the_same_dict = segments.geojson(type="segments")
