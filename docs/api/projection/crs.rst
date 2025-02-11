projection.crs module
=====================

.. _pyproj.CRS: https://pyproj4.github.io/pyproj/stable/examples.html

.. _pfdf.projection.crs:

.. py:module:: pfdf.projection.crs

    Utility functions for working with `pyproj.CRS`_ objects.

    .. dropdown:: Functions

        .. list-table::
            :header-rows: 1

            * - Function
              - Description
            * -
              -
            * - **IO**
              - 
            * - :ref:`validate <pfdf.projection.crs.validate>`
              - Checks an input represents a CRS
            * - :ref:`name <pfdf.projection.crs.name>`
              - Returns a short name describing a CRS
            * - :ref:`compatible <pfdf.projection.crs.compatible>`
              - True if two CRSs are equivalent or either CRS is None     
            * -
              -
            * - **Axes**
              -
            * - :ref:`get_axis  <pfdf.projection.crs.get_axis>`       
              - Returns the X or Y axis for a CRS
            * - :ref:`isx <pfdf.projection.crs.isx>`
              - True if a CRS axis proceeds along an east-west diration
            * - :ref:`isy <pfdf.projection.crs.isy>`
              - True if a CRS axis proceeds along a north-south direction
            * -
              -
            * - **Supported Units**
              -
            * - :ref:`supported_linear_units <pfdf.projection.crs.supported_linear_units>`
              - Returns a list of supported linear (projected) unit systems
            * - :ref:`supported_angular_units <pfdf.projection.crs.supported_angular_units>`
              - Returns a list of supported angular (geographic) unit systems
            * - :ref:`supported_units <pfdf.projection.crs.supported_units>`
              - Returns a list of supported unit systems
            * -
              -
            * - **Unit Names**
              -
            * - :ref:`xunit <pfdf.projection.crs.xunit>`
              - Returns the unit system for the X-axis
            * - :ref:`yunit <pfdf.projection.crs.yunit>`
              - Returns the unit system for the Y-axis
            * - :ref:`units <pfdf.projection.crs.units>`
              - Returns the units for the X and Y axes
            * -
              -
            * - **Unit conversions**
              -
            * - :ref:`base_to_units <pfdf.projection.crs.base_to_units>`
              - Converts a distance from axis base units to another unit system
            * - :ref:`units_to_base <pfdf.projection.crs.units_to_base>`
              - Converts a distance to axis base units from another unit system
            * -
              -
            * - **Units per meter**
              -
            * - :ref:`x_units_per_m <pfdf.projection.crs.x_units_per_m>`
              - Returns the number of X-axis base units per meter
            * - :ref:`y_units_per_m <pfdf.projection.crs.y_units_per_m>`
              - Returns the number of Y-axis base units per meter
            * - :ref:`units_per_m <pfdf.projection.crs.units_per_m>`
              - Returns the number of base units per meter for the X and Y axes
            * -
              -
            * - **Reprojection**
              -
            * - :ref:`reproject <pfdf.projection.crs.reproject>`
              - Reprojects XY coordinates from one CRS to another
            * - :ref:`utm_zone <pfdf.projection.crs.utm_zone>`
              - Returns the CRS of the best UTM zone for an XY coordinate

    The pfdf package uses `pyproj.CRS`_ objects to represent coordinate reference systems for raster and vector datasets. The package also allows some datasets to lack CRS metadata. This is to support cases where a CRS can be inferred from another dataset, such as for a numpy array derived from a Raster object. This module contains utility functions for working with `pyproj.CRS`_ objects and for cases where CRS metadata may be either a `pyproj.CRS`_ object or None.

----

IO
--

.. _pfdf.projection.crs.validate:

.. py:function:: validate(crs, strict = False)
    :module: pfdf.projection.crs

    Checks that an input represents a pyproj.CRS object or is None

    ::

        validate(crs)
        validate(crs, strict=True)

    Checks that the input either (1) represents a supported pyproj.CRS object or (2) is None. If 1, returns the input as a CRS object. Raises an error if the input is neither 1 nor 2. Set ``strict=True`` to only allow case 1 and raise an error if a CRS is None.

    :Inputs:
        * **crs** (*Any*) -- An input being validated.
        * **strict** (*bool*) -- True to require a CRS-like input. False (default) to also allow None.

    :Outputs: *pyproj.CRS | None* -- The input as a pyproj.CRS or None



.. _pfdf.projection.crs.name:

.. py:function:: name(crs)
    :module: pfdf.projection.crs

    Returns a short (one-line) name for a CRS

    ::

        name(crs)

    Returns a string with a short (one-line) name describing the CRS.

    :Inputs:
        * **crs** (*CRS-like | None*) -- A CRS-like input or None

    :Outputs: *str* -- A string describing the CRS



.. _pfdf.projection.crs.compatible:

.. py:function:: compatible(crs1, crs2)
    :module: pfdf.projection.crs

    True if two CRS options are equivalent, or either is None

    ::

        compatible(crs1, crs2)

    True if either (1) two inputs represent the same CRS, or (2) either input is None. Otherwise False.

    :Inputs:
        * **crs1** (*CRS-like*) -- A first CRS-like input
        * **crs2** (*CRS-like*) -- A second CRS-like input

    :Outputs: *bool* -- True if the two inputs represent the same CRS or either is None. Otherwise False


----

Axes
----

.. _pfdf.projection.crs.isx:

.. py:function:: isx(axis)
    :module: pfdf.projection.crs
    
    True if a pyproj Axis proceeds along an east-west axis

    ::

        isx(axis)

    True if an input ``pyproj._crs.Axis`` object proceeds along an east-west axis.

    :Inputs:
        * **axis** (*pyproj._crs.Axis*) -- A ``pyproj._crs.Axis`` object

    :Outputs: *bool* -- True if the axis proceeds along an east-west axis. Otherwise False



.. _pfdf.projection.crs.isy:

.. py:function:: isy(axis)
    :module: pfdf.projection.crs

    True if a pyproj Axis proceeds along a north-south axis

    ::

        isy(axis)

    True if an input ``pyproj._crs.Axis`` object proceeds along a north-south axis.

    :Inputs:
        * **axis** (*pyproj._crs.Axis*) -- A ``pyproj._crs.Axis`` object

    :Outputs: *bool* -- True if the axis proceeds along a north-south axis. Otherwise False



.. _pfdf.projection.crs.get_axis:

.. py:function:: get_axis(crs, axis)
    :module: pfdf.projection.crs

    Returns the requested axis for a CRS

    ::

        get_axis(crs, axis)

    Returns the requested axis for the input CRS. The ``axis`` input should be a string indicating whether to return the X or Y axis. To return the X axis, set the input to ``x``, ``dx``, ``left``, or ``right``. To return the Y axis, set the input to ``y``, ``dy``, ``bottom``, or ``top``. Returns None if the CRS does not have an axis matching the selection.

    :Inputs:
        * **crs** (*CRS-like*) -- A CRS whose axis should be returned
        * **axis** (*str*) -- A string indicating the axis that should be returned

    :Outputs: *pyproj._crs.Axis | None* -- The requested Axis for the CRS


----

Supported Units
---------------

.. _pfdf.projection.crs.supported_linear_units:

.. py:function:: supported_linear_units()
    :module: pfdf.projection.crs
    
    Returns a list of supported linear CRS unit systems

    ::

        supported_linear_units()

    Returns a list of supported linear CRS unit systems. A projected CRS will typically use a linear unit system.

    :Outputs: *list[str]* -- The names of supported linear CRS unit systems



.. _pfdf.projection.crs.supported_angular_units:

.. py:function:: supported_angular_units()
    :module: pfdf.projection.crs

    Returns a list of supported angular CRS unit systems.

    ::

        supported_angular_units()

    Returns a list of supported angular CRS unit systems. A geographic CRS will typically use an angular unit system.

    :Outputs: *list[str]* -- The names of supported angular CRS unit systems



.. _pfdf.projection.crs.supported_units:

.. py:function:: supported_units()
    :module: pfdf.projection.crs

    Returns a list of supported CRS unit systems

    ::
        
        supported_units()

    Returns a list of supported CRS unit systems. This includes both linear and angular unit systems.

    :Outputs: *list[str]* -- The names of supported CRS unit systems.


----

Unit names
----------

.. _pfdf.projection.crs.xunit:

.. py:function:: xunit(crs)
    :module: pfdf.projection.crs

    Returns the name of the X-axis unit

    ::

        xunit(crs)

    Returns the name of the CRS's X-axis unit or None if the CRS is None.

    :Inputs:
        * **crs** (*CRS-like | None*) -- A `pyproj.CRS`_ or None

    :Outputs: *str | None* -- The name of the X-axis unit


.. _pfdf.projection.crs.yunit:

.. py:function:: yunit(crs)
    :module: pfdf.projection.crs

    Returns the name of the Y-axis unit

    ::

        yunit(crs)

    Returns the name of the CRS's Y-axis unit or None if the CRS is None.

    :Inputs:
        * **crs** (*CRS-like | None*) -- A `pyproj.CRS`_ or None

    :Outputs: *str | None* -- The name of the Y-axis unit


.. _pfdf.projection.crs.units:

.. py:function:: units(crs)
    :module: pfdf.projection.crs

    Returns the name of the X and Y-axis units

    ::

        yunit(crs)

    Returns the names of the CRS's X and Y-axis units.

    :Inputs:
        * **crs** (*CRS-like | None*) -- A `pyproj.CRS`_ or None

    :Outputs: *(str, str) | (None, None)* -- The names of the X and Y axis units


----

Unit Conversions
----------------

.. _pfdf.projection.crs.base_to_units:

.. py:function:: base_to_units(crs, axis, distances, units, y = None)
    :module: pfdf.projection.crs

    Converts distances from axis base units to another unit system

    ::

        base_to_units(crs, axis, distances, units)
        base_to_units(..., y)

    Converts distances from axis base units to another unit system. See :ref:`utils.units.supported <pfdf.utils.units.supported>` for a list of supported unit systems. If converting units for an angular (geographic) coordinate system, converts units as if distances were measured at the equator. Use the ``y`` input to specify different latitudes instead. Note that y should be in axis base units.

    The ``distances`` input may be an array of any shape. If using the ``y`` input, then ``y`` should be an array that can be broadcasted against the distances. The shape of the output array will match this broadcasted shape.

    :Inputs:
        * **crs** (*CRS-like*) -- A `pyproj.CRS`_ used to convert units
        * **axis** (*str*) -- The name of the axis along which to convert 
        * **units** (*str*) -- Should be 'x' or 'y'
        * **distances** (*ndarray*) -- An array of distances in axis base units
        * **units** (*str*) -- The units that the distances should be converted to
        * **y** (*ndarray*) -- The latitudes for unit conversion for angular coordinate systems. Should be in axis base units.

    :Outputs: *numpy array* -- The distances in the specified units


.. _pfdf.projection.crs.units_to_base:

.. py:function:: units_to_base(crs, axis, distances, units, y = None)
    :module: pfdf.projection.crs

    Converts distances to axis base units

    ::

        units_to_base(crs, axis, distances, unit)
        units_to_base(..., y)

    Converts distances to axis base units from another unit system supported by pfdf. See pfdf.utils.units.supported for a list of supported unit systems. If converting units for an angular (geographic) coordinate system, converts units as if the distances were measured at the equator. Use the ``y`` input to specify a different latitudes instead. Note that y should be in axis base units.

    The ``distances`` input may be an array of any shape. If using the ``y`` input, then ``y`` should be an array that can be broadcasted against the distances. The shape of the output array will match this broadcasted shape.

    :Inputs:
        * **crs** (*CRS-like*) -- A `pyproj.CRS`_ used to convert units
        * **axis** (*str*) -- The name of the axis along which to convert units. Should be 'x' or 'y'
        * **distances** (*ndarray*) -- An array of distances that should be converted to axis base units
        * **units** (*str*) -- The units that the distances should be converted to
        * **y** (*ndarray*) -- The latitudes for unit conversion for angular coordinate systems. Should be in axis base units.

    :Outputs: *numpy array* -- The distances in axis base units


----

Units per meter
---------------

.. _pfdf.projection.crs.x_units_per_m:

.. py:function:: x_units_per_m(crs, y = None)
    :module: pfdf.projection.crs

    Returns the number of X axis units per meter

    ::

        x_units_per_m(crs)
        x_units_per_m(crs, y)

    Returns the number of X-axis units per meter. If the CRS uses an angular (geographic) coordinate system, returns the number of units per meter at the equator. Use the ``y`` input to specify different latitudes. Note that y should be in axis base units.

    :Inputs:
        * **crs** (*CRS-like*) -- The CRS being queried
        * **y** (*ndarray*) -- Specifies the latitudes for unit conversion for angular coordinate systems. Should be in axis base units

    :Outputs: *numpy array* -- The number of axis base units per meter



.. _pfdf.projection.crs.y_units_per_m:

.. py:function:: y_units_per_m(crs)
    :module: pfdf.projection.crs

    Returns the number of Y axis units per meter

    ::

        y_units_per_m(crs)

    Returns the number of Y-axis units per meter.
    
    :Inputs:
        * **crs** (*CRS-like*) -- The CRS being queried

    :Outputs: *scalar numpy array* -- The number of axis base units per meter



.. _pfdf.projection.crs.units_per_m:

.. py:function:: units_per_m(crs, y = None)
    :module: pfdf.projection.crs

    Returns the number of X and Y-axis base units per meter

    ::

        units_per_m(crs)
        units_per_m(crs, y)

    Returns the number of X and Y-axis base units per meter. If the CRS uses an angular (geographic) coordinate system, returns the number of units per meter at the equator. Use the ``y`` input to specify different latitudes. Note that y should be in axis base units.

    :Inputs:
        * **crs** (*CRS-like*) -- The CRS being queried
        * **y** (*ndarray*) -- Specifies the latitudes for unit conversion for angular coordinate systems. Should be in axis base units

    :Outputs: 
        * *numpy array* -- The number of X-axis base units per meter
        * *scalar numpy array* -- The number of Y-axis base units per meter


----

Reprojection
------------

.. _pfdf.projection.crs.reproject:

.. py:function:: reproject(from_crs, to_crs, xs, ys)
    :module: pfdf.projection.crs

    Converts X and Y coordinates from one CRS to another

    ::

        reproject(from_crs, to_crs, xs, ys)

    Reprojects X and Y coordinates from one CRS to another.

    :Inputs:
        * **from_crs** (*CRS-like*) -- The CRS that the coordinates are currently in
        * **to_crs** (*CRS-like*) -- The CRS that the coordinates should be projected to
        * **xs** (*vector*) -- The X coordinates being reprojected
        * **ys** (*vector*) -- The Y coordinates being reprojected

    :Outputs:
        * *1D numpy array* -- The reprojected X coordinates
        * *1D numpy array* -- The reprojected Y coordinates



.. _pfdf.projection.crs.utm_zone:

.. py:function:: utm_zone(crs, x, y)
    :module: pfdf.projection.crs

    Returns the best UTM CRS for the input coordinate

    ::

        utm_zone(crs, x, y)

    Returns the CRS of the best UTM zone for the input coordinate, or None if the coordinate does not have a well-defined UTM zone.

    :Inputs:
        * **crs** (*CRS-like*) -- The CRS that the coordinates are in
        * **x** (*scalar*) -- The X coordinate
        * **y** (*scalar*) -- The Y coordinate

    :Outputs: *pyproj.CRS | None* -- The CRS of the best UTM zone for the coordinate

