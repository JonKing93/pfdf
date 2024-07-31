pfdf.projection.transform module
================================

.. _pyproj.CRS: https://pyproj4.github.io/pyproj/stable/examples.html

.. _affine.Affine: https://pypi.org/project/affine/

.. _pfdf.projection.transform:

.. py:module:: pfdf.projection.transform

.. _pfdf.projection.transform.Transform:

.. py:class:: Transform
    :module: pfdf.projection.transform

    The *Transform* class implements objects that represent affine transformation matrices. These matrices are used convert the row and column indices of a raster's pixels to spatial coordinates, and take the form:

    .. math::

        \begin{vmatrix}
        dx & 0 & \mathrm{left}\\
        0 & dy & \mathrm{top}
        \end{vmatrix}

    Here, dx and dy are the change in spatial coordinate when incrementing one column or row, respectively. The "left" and "top" variables indicate the spatial coordinates of the data grid's left and top edges. The two remaining coefficients can be used to implement shear transforms. However, pfdf only supports rectangular pixels, so these will always be 0 for our purposes.

    *Transform* objects include methods to report ``dx``, ``dy``, ``left``, and ``top`` values, as well as other pixel geometry properties. An object may optionally have an associated CRS (via the ``crs`` property) which provides an absolute reference frame for the left and top coordinates. *Transform* objects support resolution values in both meters and native CRS units. Because a Transform only defines the top-left corner of a raster, the location of the raster center is unknown. As such, methods that report values derived from X-axis resolution are most accurate when an optional Y-coordinate (representing the location of the raster center) is also provided. If this coordinate is not set, X-axis resolutions are calculated as if at the equator. In addition to pixel properties, *Transform* objects include methods to reproject to other coordinate systems, and to convert to a :ref:`BoundingBox object <pfdf.projection.bbox.BoundingBox>`.

    .. dropdown:: Properties

        .. list-table::
            :header-rows: 1

            * - Property
              - Description
            * -
              -
            * - **Misc**
              - 
            * - left          
              - The spatial coordinate of the left edge
            * - top           
              - The spatial coordinate of the top edge
            * - affine        
              - The Transform as an `affine.Affine`_ object
            * - orientation   
              - The cartesian quadrant associated with the Transform. :ref:`See below <pfdf.projection.transform.Transform.orientation>` for details.
            * -
              -
            * - **CRS**
              - 
            * - crs           
              - The coordinate reference system (`pyproj.crs`_ | None)
            * - units         
              - The units along the X and Y axes
            * - xunit         
              - The X axis unit
            * - yunit         
              - The Y axis unit


    .. dropdown:: Methods

        .. list-table::
            :header-rows: 1

            * - Method
              - Description
            * -
              -
            * - **Object Creation**
              -
            * - :ref:`__init__ <pfdf.projection.transform.Transform.__init__>`      
              - Create Transform from dx, dy, left, top, and optional CRS
            * - :ref:`from_dict <pfdf.projection.transform.Transform.from_dict>`     
              - Create Transform from a keyword dict
            * - :ref:`from_list <pfdf.projection.transform.Transform.from_list>`     
              - Create Transform from a list or tuple
            * - :ref:`from_affine <pfdf.projection.transform.Transform.from_affine>`   
              - Create Transform from an `affine.Affine`_ object
            * - :ref:`copy <pfdf.projection.transform.Transform.copy>`          
              - Returns a copy of the current Transform
            * -
              -
            * - **Dunders**
              -
            * - :ref:`__repr__ <pfdf.projection.transform.Transform.__repr__>`
              - A string representing the Transform
            * - :ref:`__eq__ <pfdf.projection.transform.Transform.__eq__>`
              - True if two Transform objects have the same affine matrix and CRS
            * -
              -
            * - **Resolution**
              -
            * - :ref:`dx <pfdf.projection.transform.Transform.dx>`
              - The change in X coordinate when moving one pixel right
            * - :ref:`dy <pfdf.projection.transform.Transform.dy>`
              - The change in Y coordinate when moving one pixel down
            * - :ref:`xres <pfdf.projection.transform.Transform.xres>`
              - The X-axis resolution. Equal to the absolute value of dx
            * - :ref:`yres <pfdf.projection.transform.Transform.yres>`
              - The Y-axis resolution. Equal to the absolute value of dy
            * - :ref:`resolution <pfdf.projection.transform.Transform.resolution>`
              - An (X resolution, Y resolution) tuple
            * - 
              -
            * - **Pixel Geometries**
              -
            * - :ref:`pixel_area <pfdf.projection.transform.Transform.pixel_area>`
              - The area of a pixel
            * - :ref:`pixel_diagonal <pfdf.projection.transform.Transform.pixel_diagonal>`
              - The length of a pixel diagonal
            * -
              -
            * - **Units per meter**
              -
            * - :ref:`units_per_m <pfdf.projection.transform.Transform.units_per_m>`
              - The number of CRS units per meter along the X and Y axes
            * - :ref:`x_units_per_m <pfdf.projection.transform.Transform.x_units_per_m>`
              - The number of X axis units per meter
            * - :ref:`y_units_per_m <pfdf.projection.transform.Transform.y_units_per_m>`
              - The number of Y axis units per meter
            * -
              -
            * - **Reprojection**
              -
            * - :ref:`reproject <pfdf.projection.transform.Transform.reproject>`
              - Returns a copy of a Transform in a new CRS
            * -
              -
            * - **BoundingBox Conversion**
              -
            * - :ref:`right <pfdf.projection.transform.Transform.right>`
              - Computes the right edge, given a number of columns
            * - :ref:`bottom <pfdf.projection.transform.Transform.bottom>`
              - Computes the bottom edge, given a number of rows
            * - :ref:`bounds <pfdf.projection.transform.Transform.bounds>`
              - Converts Transform to BoundingBox, given the number of raster columns and rows
            * -
              -
            * - **As Built-in**
              -
            * - :ref:`tolist <pfdf.projection.transform.Transform.tolist>`
              - Returns a transform as a list
            * - :ref:`todict <pfdf.projection.transform.Transform.todict>`
              - Returns a transform as a dict
            * -
              -
            * - **Testing**
              -
            * - :ref:`isclose <pfdf.projection.transform.Transform.isclose>`
              - True if an input is a Transform with similar values

----

Properties
----------

Misc
++++

.. py:property:: Transform.left

    The spatial coordinate of the left edge

.. py:property:: Transform.top
    
    The spatial coordinate of the top edge

.. py:property:: Transform.affine
    
    The Transform as an `affine.Affine`_ object

.. _pfdf.projection.transform.Transform.orientation:

.. py:property:: Transform.orientation
    
    The cartesian quadrant associated with the Transform. This is the quadrant of the Cartesian plane that would contain a Transform's raster if the origin point is defined as the raster's minimum X and minimum Y coordinate. As follows:

    .. list-table::
        :header-rows: 1

        * - Quadrant
          - dx
          - dy
        * - 1
          - Positive
          - Negative
        * - 2
          - Negative
          - Negative
        * - 3
          - Negative
          - Positive
        * - 4
          - Positive
          - Positive


CRS
+++

.. py:property:: Transform.crs
    
    The coordinate reference system (`pyproj.crs`_ | None)

.. py:property:: Transform.units
    
    The units along the X and Y axes

.. py:property:: Transform.xunit
    
    The X axis unit

.. py:property:: Transform.yunit

    The Y axis unit

----

Object Creation
---------------

.. _pfdf.projection.transform.Transform.__init__:

.. py:method:: Transform.__init__(self, dx, dy, left, top, crs = None)

    Creates a new Transform object

    ::

        Transform(dx, dy, left, top)
        Transform(..., crs)

    Creates a new Transform from the affine parameters and optional CRS.

    :Inputs:
        * **dx** (*float*) - The change in X-coordinate when moving one pixel right
        * **dy** (*float*) - The change in Y-coordinate when moving one pixel down
        * **left** (*float*) - The spatial coordinate of the left edge
        * **top** (*float*) - The spatial coordinate of the top edge
        * **crs** (*CRS-like*)- The coordinate reference system for the Transform. Must be convertible to a `pyproj.CRS`_ object

    :Outputs:
        *Transform* - The new Transform object


.. _pfdf.projection.transform.Transform.from_affine:

.. py:method:: Transform.from_affine(input, crs = None)

    Creates a Transform from an `affine.Affine`_ object

    ::

        Transform.from_affine(input)
        Transform.from_affine(input, crs)

    Creates a Transform from an `affine.Affine`_ object. The affine object must have scalar real-valued coefficients, and cannot implement a shear transformation. Equivalently, the "b" and "d" coefficients must be 0. Affine objects do not include CRS information, so use the "crs" option to also probide a CRS.

    :Inputs:
        * **input** (*affine.Affine*) - The `affine.Affine`_ object used to create the Transform
        * **crs** (*CRS-like*) - A CRS input for the transform

    :Outputs:
        *Transform* - The new Transform object


.. _pfdf.projection.transform.Transform.from_dict:

.. py:method:: Transform.from_dict(cls, input)

    Builds a Transform from a keyword dict

    ::
      
        Transform.from_dict(input)

    Builds a Transform object from a keyword dict. The dict may have either 4 or 5 keys, and each key must be a string. The dict must include the four keys: "dx", "dy", "left", and "top", and the value for each of those keys should be a float. The dict may optionally include a "crs" key, which will be used to add CRS information to the object.

    :Inputs: **input** (*dict*) -- A dict used to create a Transform

    :Outputs: *Transform* -- A Transform created from the input dict


.. _pfdf.projection.transform.Transform.from_list:

.. py:method:: Transform.from_list(input)

    Creates a Transform from a list or tuple

    ::
        
        Transform.from_list(input)

    Creates a Transform from a list or tuple. The input may have 4, 5, 6, or 9 elements. If 6 or 9, the list is used to initialize an `affine.Affine`_ object, and the Affine object used to derive the transform. If 4 or 5 elements, then the elements are interpreted as the arguments to the constructor (dx, dy, left, top, crs).

    :Inputs:
        * **input** (*list | tuple*) - The list or tuple used to create the Transform

    :Outputs:
        *Transform* - The new Transform object


.. _pfdf.projection.transform.Transform.copy:

.. py:method:: Transform.copy(self)

    Returns a copy of the current Transform

    ::
      
        self.copy()

    Returns a copy of the current Transform with the same values and CRS.

    :Outputs: *Transform* -- A copy of the current Transform

----

Dunders
-------

.. _pfdf.projection.transform.Transform.__repr__:

.. py:method::  Transform.__repr__(self)

    String representation including affine matrix values and CRS name.

    ::

        repr(self)
        str(self)

    :Output: *str* -- String representation of the Transform


.. _pfdf.projection.transform.Transform.__eq__:

.. py:method:: Transform.__eq__(self, other)

    True if other is a Transform with the same affine matrix values and CRS

    ::

        self == other

    :Outputs: *bool* -- True if the other object is a Transform with the same affine matrix values and CRS.


----

Resolution
----------

.. _pfdf.projection.transform.Transform.dx:

.. py:method:: Transform.dx(self, units = "base", y = None)
    
    Return the change in X coordinate when moving one pixel right

    ::

        self.dx()
        self.dx(units)
        self.dx(units, y)

    Returns the change in X coordinate when moving one pixel right. By default, returns dx in the base unit of the CRS. Use the ``units`` option to return dx in other units instead. Supported units include "meters", "kilometers",  "feet", and "miles". Note that these options are only supported when the Transform has a CRS. If the Transform uses a geographic (angular) coordinate system, converts dx to the specified units as if dx were measured along  the equator. Use the ``y`` input to specify a different latitude for unit conversion. Note that y should be in the base units of the CRS.

    :Inputs:
        * **units** (*str*) -- The units that dx should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"
        * **y** (*scalar*) -- An optional y coordinate (in the units of the CRS) indicating the latitude at which dx is being assessed. Ignored if the CRS is not geographic (angular). Defaults to the equator

    :Outputs:
        *float* -- The dx for the transform
        

.. _pfdf.projection.transform.Transform.dy:

.. py:method:: Transform.dy(self, units = "base")

    Return the change in Y coordinate when moving one pixel down

    ::

        self.dy()
        self.dy(units)

    Returns the change in Y coordinate when moving one pixel down. By default, returns the distance in the base unit of the transform. Use the ``units`` option to return the distance in specific units instead. This option is only available when the Transform has a CRS. Supported units include "meters", "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units that dy should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The dy for the transform


.. _pfdf.projection.transform.Transform.xres:

.. py:method:: Transform.xres(self, units = "base", y = None)

    Return pixel resolution along the X axis

    ::

        self.xres()
        self.xres(units)
        self.xres(units, y)

    Returns the pixel resolution along the X axis (the absolute value of dx). By default, returns xres in the base units of the CRS. Use the ``units`` option to return xres in other units instead. Supported units include "meters", "kilometers", "feet", and "miles". Note that these options are only supported when the Transform has a CRS. If the Transform uses a geographic (angular) coordinate  system, converts xres to the specified units as if xres were measured along the equator. Use the ``y`` input to specify a different latitude for unit conversion. Note that y should be in the base units of the CRS.

    :Inputs:
        * **units** (*str*) -- The units that xres should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"
        * **y** (*scalar*) -- An optional y coordinate (in the units of the CRS) indicating the latitude at which xres is being assessed. Ignored if the CRS is not geographic (angular). Deafults to the equator

    :Outputs:
        *float* -- The X resolution for the Transform
        

.. _pfdf.projection.transform.Transform.yres:

.. py:method:: Transform.yres(self, units = "base")

    Return pixel resolution along the Y axis

    ::

        self.yres()
        self.yres(units)

    Returns the pixel resolution along the Y axis. This is the absolute value of dy. By default, returns resolution in the base unit of the Transform. Use the ``units`` option to return yres in the specified units instead. This option is only available when the Transform has a CRS. Supported units include: "meters", "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units that yres should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The Y resolution for the Transform
        

.. _pfdf.projection.transform.Transform.resolution:

.. py:method:: Transform.resolution(self, units = "base", y = None)

    Return pixel resolution

    ::

        self.resolution()
        self.resolution(units)
        self.resolution(units, y)

    Returns the pixel resolution for the Transform as an (X res, Y res) tuple. By default, returns resolution in the base units of the Transform CRS. Use the ``units`` option to return resolution in the specified units instead. Supported units include "meters", "kilometers", "feet", and "miles". Note that these options are only supported when the Transform has a CRS. If the Transform uses a geographic (angular) coordinate system, converts resolution to the specified units as if resolution were measured along the equator. Use the ``y`` input to specify a different latitude for unit conversion. Note that y should be in the base units of the CRS.

    :Inputs:
        * **units** (*str*) -- The units that resolution should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"
        * **y** (*scalar*) -- An optional y coordinate (in the units of the CRS) indicating the latitude at which xres is being assessed. Ignored if the CRS is not geographic (angular). Defaults to the equator

    :Outputs:
        *float, float* -- The (X, Y) resolution for the Transform


----

Pixel geometries
----------------

.. _pfdf.projection.transform.Transform.pixel_area:

.. py:method:: Transform.pixel_area(self, units = "base", y = None)

    Returns the area of a pixel for the Transform

    ::

        self.pixel_area()
        self.pixel_area(units)
        self.pixel_area(units, y)

    Returns the area of a pixel for the Transform. By default, returns area in the units of the CRS squared. Use the ``units`` option to return area in the specified units instead. Supported units include: "meters", "kilometers", "feet", and "miles". This option is only available when the Transform has  a CRS. If the Transform uses a geographic (angular) coordinate system,  converts area to the indicated units as if x-resolution were measured along the equator. Use the ``y`` input to specify a different latitude for unit conversion. Note that y should be in the base units of the CRS.

    :Inputs:
        * **units** (*str*) -- The (squared) units that pixel_area should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"
        * **y** (*scalar*) -- An optional y coordinate (in the units of the CRS) indicating the latitude at which xres is being assessed. Ignored if the CRS is not geographic (angular). Defaults to the equator

    :Outputs:
        *float* -- The area of a pixel in the Transform


.. _pfdf.projection.transform.Transform.pixel_diagonal:

.. py:method:: Transform.pixel_diagonal(self, units = "base", y = None)

    Returns the area of a pixel for the Transform

    ::

        self.pixel_diagonal()
        self.pixel_diagonal(units)
        self.pixel_diagonal(units, y)

    Returns the length of a pixel diagonal for the Transform. By default, returns length in the units of the CRS squared. Use the ``units`` option to return length in the specified units instead. Supported units include: "meters", "kilometers", "feet", and "miles". This option is only available when the Transform has  a CRS. If the Transform uses a geographic (angular) coordinate system, converts length to the indicated units as if x-resolution were measured along the equator. Use the ``y`` input to specify a different latitude for unit conversion. Note that y should be in the base units of the CRS.

    :Inputs:
        * **units** (*str*) -- The units that the length should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"
        * **y** (*scalar*) -- An optional y coordinate (in the units of the CRS) indicating the latitude at which xres is being assessed. Ignored if the CRS is not geographic (angular). Defaults to the equator

    :Outputs:
        *float* -- The length of a pixel diagonal in the Transform
        


----

Units per meter
---------------


.. _pfdf.projection.transform.Transform.x_units_per_m:

.. py:method:: Transform.x_units_per_m(self, y = None)

    Returns the number of X axis units per meter

    ::

        self.x_units_per_m()
        self.x_units_per_m(y)

    Returns the number of X axis units per meter. None if the Transform does not have a CRS. If the Transofrm uses an angular (geographic) CRS, converts units to meters as if along the equator. Use the "y" input to specify a different latitude for meters conversion. Note that y should be in the base units of the CRS.

    :Inputs:
        * **y** (*float*) - An optional Y coordinate (in the units of the CRS) indicating the latitude at which meters converson is assessed. Ignored if the CRS is not angular (geographic). Defaults to the equator.

    :Outputs:
        *float | None* - The number of X axis units per meter


.. _pfdf.projection.transform.Transform.y_units_per_m:

.. py:method:: Transform.y_units_per_m(self)

    Returns the number of Y units per meter

    ::

        self.y_units_per_m()

    Returns the number of Y axis units per meter, or None if the Transform does not have a CRS.

    :Outputs:
        *float | None* - The number of Y axis units per meter.


.. _pfdf.projection.transform.Transform.units_per_m:

.. py:method:: Transform.units_per_m(self, y = None)

    Returns the number of units per meter along the X and Y axes

    ::

        self.units_per_m()
        self.units_per_m(y)

    Returns the number of CRS axis units per meter. None if the Transform does not have a CRS. Otherwise, returns a tuple with the values for the X and Y axes, respectively. If the Transform uses an angular (geographic) CRS, converts units to meters as if along the equator. Use the "y" input to specify a different latitude for meters conversion. Note that y should be in the units of the CRS.

    :Inputs:
        * **y** (*float*) - An optional Y coordinate (in the units of the CRS) indicating the latitude at which meters conversion is assessed. Ignored if the CRS is not angular (geographic). Defaults to the equator.

    :Outputs:
        *float | None* - The conversion factor for the X axis (or None if the Transform does not have a CRS)
        *float | None* - The conversion factor for the Y axis (or None if the Transform does not have a CRS)

----

Reprojection
------------


.. _pfdf.projection.transform.Transform.reproject:

.. py:method:: Transform.reproject(self, crs, y = None)

    Reprojects the Transform into a different CRS

    ::

        self.reproject(crs)
        self.reproject(crs, y)

    Reprojects the Transform into a different CRS. By default, reprojects the  Transform as for a dataset located at the equator. Use the "y" input to specify a different latitude for reprojection. Note that y should be in the base unit of the current CRS.

    :Inputs:
        * **crs** (*CRS-like*) - The CRS in which to reproject the Transform
        * **y** (*float*) - The Y coordinate at which to perform the reprojection. Defaults to the equator.

    :Outputs:
        *Transform* - The reprojected Transform


----

Bounds Conversion
-----------------

.. _pfdf.projection.transform.Transform.right:

.. py:method:: Transform.right(self, ncols)

    Compute the right edge of a bounding box

    ::

        self.right(ncols)

    Computes the locates of the right edge of a raster with the given number of columns for the Transform.

    :Inputs:
        * **ncols** (*float*) - The number of raster columns

    :Outputs:
        *float* - The spatial coordinate of the raster's right edge


.. _pfdf.projection.transform.Transform.bottom:

.. py:method:: Transform.bottom(self, nrows)

    Compute the bottom edge of a bounding box

    ::

        self.bottom(nrows)

    Computes the locates of the bottom edge of a raster with the given number of rows for the Transform.

    :Inputs:
        * **nrows** (*float*) - The number of raster rows

    :Outputs:
        *float* - The spatial coordinate of the raster's bottom edge


.. _pfdf.projection.transform.Transform.bounds:

.. py:method:: Transform.bounds(self, nrows, ncols)

    bounds  Returns a BoundingBox object derived from the Transform

    ::

        self.bounds(nrows, ncols)

    Converts the Transform to a BoundingBox object, given a number of raster rows and columns.

    :Inputs:
        * **nrows** (*float*) - The number of raster rows
        * **ncols** (*float*) - The number of raster columns

    :Outputs:
        *BoundingBox* - A BoundingBox object derived from the Transform


----

As Built-In
-----------

.. _pfdf.projection.transform.Transform.tolist:

.. py:method:: Transform.tolist(self, crs = True)

    Returns a Transform as a list

    ::

        self.tolist()
        self.tolist(crs=False)

    Returns the current Transform as a list. By default, the list will have 5 elements. The first four elements are dx, dy, left, and top (in that order). The fifth element is the CRS information. Set crs=False to exclude the CRS information and return a list with only 4 elements.

    :Inputs:
        * **crs** (*bool*) -- True (default) to return CRS information as the 5th element. False to exclude CRS information and return a list with 4 elements.

    :Outputs: *list* -- The Transform as a list

.. _pfdf.projection.transform.Transform.todict:

.. py:method:: Transform.todict(self)

    Returns a Transform as a dict

    ::
      
        self.todict()

    Returns the Transform as a dict. The dict will have 5 keys. The first four are "dx", "dy", "left", and "top". The 5th key is "crs" and holds the associated CRS information.

    :Outputs: *dict* -- The Transform as a dict


----

Testing
-------

.. _pfdf.projection.transform.Transform.isclose:

.. py:method:: Transform.isclose(self, other, rtol = 1e-5, atol = 1e-8)

    True if two Transform objects are similar

    .. dropdown:: Test Similarity

        ::
        
            self.isclose(other)

        Tests if another Transform object has similar values to the current object. Compares both the CRSs and the affine matrix values. Uses numpy.allclose to compare the 4 affine matrix values. True if numpy.allclose return True AND the two objects have compatible CRSs. (Two CRSs are compatible if the two CRSs are equal, or at least one CRS is None).

    .. dropdown:: Set Tolerance

        ::

            self.isclose(..., rtol, atol)

        Specify the relative tolerance and absolute tolerance for the numpy.allclose check. By default, uses a relative tolerance of 1E-5, and an absolute tolerance of 1E-8.

    :Inputs:
        * **other** (*Transform*) -- Another Transform object
        * **rtol** (*scalar*) -- The relative tolerance for float comparison. Defaults to 1E-5.
        * **atol** (*scalar*) -- The absolute tolerance for float comparison. Defaults to 1E-8

    :Outputs: *bool* -- True if the other Transform is similar to the current object



