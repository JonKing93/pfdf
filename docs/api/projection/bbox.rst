projection.BoundingBox class
============================

.. _pyproj.CRS: https://pyproj4.github.io/pyproj/stable/examples.html

.. _pfdf.projection.BoundingBox:

.. py:class:: BoundingBox
    :module: pfdf.projection

    The *BoundingBox* class implements rectangular bounding boxes. These objects are typically used to locate the edges of raster datasets. The ``left``, ``right``, ``top``, and ``bottom`` properties record the coordinates of a *BoundingBox* object's edges. A box may optionally have an associated CRS (via the ``crs`` property) which provides an absolute reference frame for the coordinates. *BoundingBox* objects also include methods to locate a box's center, measure a box's height or width, reproject the box into other coordinate systems, and convert the box to a :ref:`Transform object <pfdf.projection.Transform>`.
    
    .. dropdown:: Properties

        .. list-table::
            :header-rows: 1

            * - Property
              - Description
            * -
              -
            * - **Edges**
              -
            * - left            
              - The left coordinate
            * - right         
              - The right coordinate
            * - bottom       
              - The bottom coordinate
            * - top           
              - The top coordinate
            * -
              - 
            * - **Edge Tuples**
              -
            * - xs            
              - A (left, right) tuple
            * - ys            
              - A (bottom, top) tuple
            * - bounds        
              - A (left, bottom, right, top) tuple
            * -
              - 
            * - **Center**
              -
            * - center        
              - The (X, Y) coordinate of the box's center
            * - center_x      
              - The X coordinate of the box's center
            * - center_y      
              - The Y coordinate of the box's center
            * -
              - 
            * - **Orientation**
              -
            * - orientation   
              - The Cartesian quadrant of the box's orientation. See :ref:`below <pfdf.projection.BoundingBox.orient>` for details.
            * -
              - 
            * - **CRS**
              -
            * - crs           
              - Coordinate reference system (`pyproj.CRS`_ or None)
            * - units         
              - The units of the X and Y axes
            * - xunit         
              - The unit of the CRS X axis
            * - yunit         
              - The unit of the CRS Y axis
            * -
              - 
            * - **Units per meter**
              -
            * - units_per_m   
              - The number of CRS units per meter along the X and Y axes
            * - x_units_per_m 
              - The number of CRS X units per meter
            * - y_units_per_m   
              - The number of CRS Y units per meter    
    
    
    .. dropdown:: Methods

        .. list-table::
            :header-rows: 1

            * - Method
              - Description
            * -
              -
            * - **Object Creation**
              -
            * - :ref:`__init__ <pfdf.projection.BoundingBox.__init__>`
              - Creates a new BoundingBox from edge coordinates and optional CRS
            * - :ref:`from_list <pfdf.projection.BoundingBox.from_list>`
              - Creates a BoundingBox from a list or tuple of edge coordinates and optional CRS
            * - :ref:`from_dict <pfdf.projection.BoundingBox.from_dict>`
              - Creates a BoundingBox from a dict
            * - :ref:`copy <pfdf.projection.BoundingBox.copy>`
              - Returns a copy of the current BoundingBox
            * -
              -
            * - **Dunders**
              -
            * - :ref:`__repr__ <pfdf.projection.BoundingBox.__repr__>`
              - A string representing the BoundingBox
            * - :ref:`__eq__ <pfdf.projection.BoundingBox.__eq__>`
              - True if two BoundingBox objects have the same edge coordinates and CRS
            * -
              -
            * - **Axis Lengths**
              -
            * - :ref:`xdisp <pfdf.projection.BoundingBox.xdisp>`
              - Right minus Left
            * - :ref:`ydisp <pfdf.projection.BoundingBox.ydisp>`
              - Top minus bottom
            * - :ref:`width <pfdf.projection.BoundingBox.width>`
              - Absolute value of xdisp
            * - :ref:`height <pfdf.projection.BoundingBox.height>`
              - Absolute value of ydisp
            * -
              -
            * - **Misc**
              -
            * - :ref:`orient <pfdf.projection.BoundingBox.orient>`
              - Returns a copy of the box in the requested orientation
            * - :ref:`buffer <pfdf.projection.BoundingBox.buffer>`
              - Buffers the edges of the box by the indicated distance(s)
            * -
              -
            * - **Reprojection**
              -
            * - :ref:`utm_zone <pfdf.projection.BoundingBox.utm_zone>`
              - Returns the best UTM CRS for the box's center
            * - :ref:`reproject <pfdf.projection.BoundingBox.reproject>`
              - Returns a copy of the box projected into a different CRS
            * - :ref:`to_utm <pfdf.projection.BoundingBox.to_utm>`
              - Returns a copy of the box projected into the best UTM zone
            * - :ref:`to_4326 <pfdf.projection.BoundingBox.to_4326>`
              - Returns a copy of the box projected into EPSG:4326
            * -
              -
            * - **CRS Operations**
              -
            * - :ref:`match_crs <pfdf.projection.BoundingBox.match_crs>`
              - Returns a copy of the box compatible with an input CRS
            * - :ref:`remove_crs <pfdf.projection.BoundingBox.remove_crs>`
              - Returns a copy of the BoundingBox without a CRS
            * -
              -
            * - **Transform Conversion**
              -
            * - :ref:`dx <pfdf.projection.BoundingBox.dx>`
              - Pixel dx given a number of columns
            * - :ref:`dy <pfdf.projection.BoundingBox.dy>`
              - Pixel dy given a number of rows
            * - :ref:`transform <pfdf.projection.BoundingBox.transform>`
              - Converts the box to a Transform
            * -
              -
            * - **As built-in**
              -
            * - :ref:`tolist <pfdf.projection.BoundingBox.tolist>`
              - Returns the box as a list
            * - :ref:`todict <pfdf.projection.BoundingBox.todict>`
              - Returns the box as a dict
            * -
              -
            * - **Testing**
              -
            * - :ref:`isclose <pfdf.projection.BoundingBox.isclose>`
              - True if a second BoundingBox has similar values

----

Properties
----------

Edges
+++++

.. py:property:: BoundingBox.left

    The left coordinate

.. py:property:: BoundingBox.right

    The right coordinate

.. py:property:: BoundingBox.bottom

    The bottom coordinate

.. py:property:: BoundingBox.top

    The top coordinate


Edge Tuples
+++++++++++

.. py:property:: BoundingBox.xs

    A (left, right) tuple

.. py:property:: BoundingBox.ys

    A (bottom, top) tuple

.. py:property:: BoundingBox.bounds

    A (left, bottom, right, top) tuple


Center
++++++

.. _pfdf.projection.BoundingBox.center:

.. py:property:: BoundingBox.center
  
    The (X, Y) coordinate of the box's center

.. py:property:: BoundingBox.center_x
  
    The X coordinate of the box's center

.. py:property:: BoundingBox.center_y
  
    The Y coordinate of the box's center


Orientation
+++++++++++

.. py:property:: BoundingBox.orientation
  
    The Cartesian quadrant of the box's orientation. See :ref:`below <pfdf.projection.BoundingBox.orient>` for details.


CRS
+++

.. py:property:: BoundingBox.crs
  
  Coordinate reference system (`pyproj.CRS`_ | None)

.. py:property:: BoundingBox.units
  
    The units of the X and Y axes

.. py:property:: BoundingBox.xunit
  
    The unit of the CRS X axis

.. py:property:: BoundingBox.yunit
  
    The unit of the CRS Y axis


Units per meter
+++++++++++++++

.. py:property:: BoundingBox.units_per_m
  
  The number of CRS units per meter along the X and Y axes
  
.. py:property:: BoundingBox.x_units_per_m
  
    The number of CRS X units per meter

.. py:property:: BoundingBox.y_units_per_m
  
    The number of CRS Y units per meter
  

----

Object Creation
---------------

.. _pfdf.projection.BoundingBox.__init__:

.. py:method:: BoundingBox.__init__(self, left, bottom, right, top, crs = None)

    Creates a new bounding box object

    ::

        BoundingBox(left, bottom, right, top)
        BoundingBox(..., crs)

    Creates a new BoundingBox from the indicated edge coordinates and an optional coordinate reference system.

    :Inputs:
        * **left**, **bottom**, **right**, **top** (*scalar*) -- The edges of the new BoundingBox. Each coordinate must be a scalar numeric value.
        * **crs** (*CRS-like*) -- The coordinate reference system for the bounding box. Must be convertible to a `pyproj.CRS`_ object via the standard API.

    :Outputs: *BoundingBox*: The new BoundingBox object


.. _pfdf.projection.BoundingBox.from_dict:

.. py:method:: BoundingBox.from_dict(cls, input)

    Builds a BoundingBox from a keyword dict

    ::
      
        BoundingBox.from_dict(input)

    Builds a BoundingBox object from a keyword dict. The dict may have either 4 or 5 keys, and each key must be a string. The dict must include the four keys: "left", "right", "bottom", and "top", and the value for each of those keys should be a float. The dict may optionally include a "crs" key, which will be used to add CRS information to the object.

    :Inputs: **input** (*dict*) -- A dict used to create a BoundingBox

    :Outputs: *BoundingBox* -- A BoundingBox created from the input dict


.. _pfdf.projection.BoundingBox.from_list:

.. py:method:: BoundingBox.from_list(cls, input)

    Creates a BoundingBox from a list or tuple

    ::

        BoundingBox.from_list(input)

    Creates a BoundingBox from an input list or tuple. The input may have either 4 or 5 or five elements. The first four elements should be floats and correspond to the left, bottom, right, and top edge coordinates (in that order). The optional fifth element should be a value used to add CRS information to the object.

    :Inputs:
        * **input** (*list | tuple*): A list or tuple with either 4 or 5 elements.

    :Outputs: *BoundingBox* -- A BoundingBox object created from the list

.. _pfdf.projection.BoundingBox.copy:

.. py:method:: BoundingBox.copy(self)

    Returns a copy of the current BoundingBox

    ::
      
        self.copy()

    Returns a copy of the BoundingBox with the same values and CRS.

    :Outputs: *BoundingBox* -- A copy of the current BoundingBox


----

Dunders
-------

.. _pfdf.projection.BoundingBox.__repr__:

.. py:method::  BoundingBox.__repr__(self)

    String representation including class name, edge coordinates, and CRS name.

    ::

        repr(self)
        str(self)

    :Output: *str* -- String representation of the BoundingBox

.. _pfdf.projection.BoundingBox.__eq__:

.. py:method:: BoundingBox.__eq__(self, other)

    True if other is a BoundingBox with the same edge coordinates and CRS

    ::

        self == other

    :Outputs: *bool* -- True if the other object is a BoundingBox with the same edge coordinates and CRS.



----

Axis Lengths
------------
       
  
.. _pfdf.projection.BoundingBox.xdisp:

.. py:method:: BoundingBox.xdisp(self, units = "base")

    Returns the change in X-coordinate (displacement) from left to right

    ::

        self.xdisp()
        self.xdisp(units)

    Returns the X-coordinate displacement (right - left). By default, returns xdisp in the base unit of the X axis. Use the ``units`` option to specify the units instead. Note that this option is only available when the BoundingBox has a CRS. Supported units include: "meters", "kilometers", "feet", and "miles".

    :Inputs:
         * **units** (*str*) -- The units that xdisp should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The change in X coordinate (right - left)


.. _pfdf.projection.BoundingBox.ydisp:

.. py:method:: BoundingBox.ydisp(self, units = "base")

    Returns the change in Y-coordinate (displacement) from bottom to top

    ::

        self.ydisp()
        self.ydisp(units)

    Returns the Y-coordinate displacement (top - bottom). By default, returns ydisp in the base units of the Y axis. Use the ``units`` option to specify the units instead. Note that this option is only supported when the BoundingBox has a CRS. Supported units include: "meters", "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units that ydisp should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The change in Y coordinate (right - left)


.. _pfdf.projection.BoundingBox.width:

.. py:method:: BoundingBox.width(self, units = "base")

    Returns the length of the BoundingBox along the X-axis

    ::

        self.width()
        self.width(units)

    Returns the length of the BoundingBox along the X-axis. By default, returns the width in the CRS base unit. Use the ``units`` option to specify the units instead. Note that this option is only supported when the BoundingBox has a CRS. Supported units include: "meters", "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units that width should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The length of the box along the X-axis


.. _pfdf.projection.BoundingBox.height:

.. py:method:: BoundingBox.height(self, units = "base")

    Returns the length of the BoundingBox along the Y-axis

    ::

        self.height()
        self.height(units)
        
    Returns the length of the BoundingBox along the Y-axis. By default, returns the height in the CRS base unit. Use the ``units`` option to specify the units instead. Note that this option is only supported when the BoundingBox has a CRS. Supported units include: "meters", "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units that height should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The length of the box along the Y-axis
        
----

Orientation
-----------

.. _pfdf.projection.BoundingBox.orient:

.. py:method:: BoundingBox.orient(self, quadrant = 1)
        
    Returns a copy of the BoundingBox in the requested orientation
    
    ::

        self.orient(quadrant)

    Returns a copy of the BoundingBox in the requested orientation. The input should be either 1, 2, 3, or 4, and represent the quadrant of the Cartesian plane that would contain the box when the origin point is defined as the box's minimum X and minimum Y coordinate. As follows:

    .. list-table::
      :header-rows: 1

      * - Quadrant
        - Horizontal
        - Vertical
      * - 1
        - left <= right
        - bottom <= top
      * - 2
        - left > right
        - bottom <= top
      * - 3
        - left > right
        - bottom > top
      * - 4
        - left <= right
        - bottom > top
    
    :Inputs:
        * **quadrant** (*1|2|3|4*) -- The orientation of the output BoundingBox

    :Outputs: *BoundingBox* -- A copy of the BoundingBox in the requested orientation
        

----

Buffering
---------

.. _pfdf.projection.BoundingBox.buffer:

.. py:method:: BoundingBox.buffer(self, distance = None, units = "base", *, left = None, bottom = None, right = None, top = None)
        
    Buffers the edges of a BoundingBox
    
    .. dropdown:: Buffer

        ::

            self.buffer(distance)
            self.buffer(distance, units)

        Returns a copy of the box for which the edges have been buffered by the indicated distance. Note that distance must be positive. By default, distances are interpreted as the base unit of the bounding box. Use the ``units`` option to specify the units of the input distance instead. Note that this option is only available when the box has a CRS. Supported units include: "meters", "kilometers", "feet", and "miles".


    .. dropdown:: Specific Edges

        ::

            self.buffer(..., *, left, bottom, right, top)

        Specifies buffers for specific edges of the box. Use the keyword options to implement different buffers along different edges. If a keyword option is not specified, uses the default buffer from the 'distance' input for the associated edge. If distance is not provided, uses a default buffering distance of 0.
    
    :Inputs:
        * **distance** (*scalar*) -- The default buffering distance for the box edges
        * **units** (*str*) -- The units of the input buffering distances. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"
        * **left** (*scalar*) -- The buffer for the left edge
        * **bottom** (*scalar*) -- The buffer for the bottom edge
        * **right** (*scalar*) -- The buffer for the right edge
        * **top** (*scalar*) -- The buffer for the top edge

    :Outputs: *BoundingBox* -- A BoundingBox with buffered edges
        

----

Reprojection
------------

.. _pfdf.projection.BoundingBox.utm_zone:

.. py:method:: BoundingBox.utm_zone(self)
        
    Returns the CRS of the best UTM zone for the box's center point
    
    ::

        self.utm_zone()

    Returns the `pyproj.CRS`_ of the best UTM zone for the box's center point. The best UTM zone is whichever zone contains the center point. If the point is exactly on the border of multiple UTM zones, then returns one of the zones arbitrarily. Returns None if the point is not within a UTM zone (typically high-latitude polar regions). This method is only available when a BoundingBox has a CRS.
    
    :Outputs: *pyproj.CRS | None* -- The best UTM CRS for the box's center point
        

.. _pfdf.projection.BoundingBox.reproject:

.. py:method:: BoundingBox.reproject(self, crs)
        
    Returns a copy of a BoundingBox projected into the indicated CRS
    
    ::

        self.reproject(crs)

    Returns a copy of the bounding box reprojected into a new CRS. Note that this method is only available when a BoundingBox has a CRS.
    
    :Inputs:
        * **crs** (*CRS-like*) -- The CRS of the reprojected BoundingBox

    :Outputs: *BoundingBox* -- The reprojected box
        

.. _pfdf.projection.BoundingBox.to_utm:

.. py:method:: BoundingBox.to_utm(self)
        
    Returns a copy of the BoundingBox in the best UTM zone
    
    ::

        self.to_utm()

    Returns a copy of a box reprojected into the best UTM zone for the box's center coordinate. Only available when a BoundingBox has a CRS. Raises a ValueError if the box's center coordinate is not within the UTM domain.
    
    :Outputs: *BoundingBox* -- The reprojected BoundingBox
        

.. _pfdf.projection.BoundingBox.to_4326:

.. py:method:: BoundingBox.to_4326(self)
        
    Returns a copy of the BoundingBox in EPSG:4326
    
    ::

        self.to_4326()

    Returns a copy of a BoundingBox reprojected into EPSG:4326 (often referred to as WGS 84). This method is only available when a BoundingBox has a CRS.
    
    :Outputs: *BoundingBox* -- The reprojected BoundingBox


----

CRS Operations
--------------

.. _pfdf.projection.BoundingBox.match_crs:

.. py:method:: BoundingBox.match_crs(self, crs)

    Returns a copy of the BoundingBox whose CRS is compatible with a CRS-like input

    ::

        self.match_crs(crs)

    Returns an object whose CRS is compatible with a CRS-like input. If the ``crs`` input is None, returns the current object. If the current object does not have a CRS, returns an object whose CRS has been updated to match the input. Otherwise, reprojects the object to match the input CRS.

    :Inputs:
        * **crs** (*CRS-like*) -- A CRS-like input or None

    :Outputs: *BoundingBox* -- A BoundingBox compatible with the input CRS


.. _pfdf.projection.BoundingBox.remove_crs:

.. py:method:: BoundingBox.remove_crs(self)

    Returns a copy of the current BoundingBox that does not have a CRS

    ::

        self.remove_crs()

    Returns a copy of the current BoundingBox whose CRS is set to None.

    :Outputs:
        *BoundingBox* -- A copy of the current BoundingBox without a CRS


----

Transform Conversion
--------------------

.. _pfdf.projection.BoundingBox.dx:

.. py:method:: BoundingBox.dx(self, ncols, units = "base")
        
    Computes pixel spacing, given a number of raster columns
    
    ::

        self.dx(ncols)
        self.dx(ncols, units)

    Computes the pixel spacing required to fit an input number of columns into the *BoundingBox*. By default, returns spacing in the base unit of the CRS. Use the ``units`` option to specify the units instead. Note that this option is only available when the *BoundingBox* has a CRS. Supported units include: "meters", "kilometers", "feet", and "miles".
    
    :Inputs:
        * **ncols** (*int*) -- The number of columns in a raster
        * **units** (*str*) -- The units that dx should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"

    :Outputs: *float* -- The computed pixel spacing
        

.. _pfdf.projection.BoundingBox.dy:

.. py:method:: BoundingBox.dy(self, nrows, units = "base")
        
    Computes pixel spacing, given a number of raster rows
    
    ::

        self.dy(nrows)
        self.dy(nrows, units)

    Computes the pixel spacing required to fit an input number of rows into the *BoundingBox*. By default, returns spacing in the base unit of the CRS. Use the ``units`` option to specify the units instead. Note that this option is only available when the *BoundingBox* has a CRS. Supported units include: "meters", "kilometers", "feet", and "miles".
    
    :Inputs:
        * **nrows** (*int*) -- The number of rows in a raster
        * **units** (*str*) -- The units that dy should be returned in. Options include: "base" (default; CRS base units), "meters", "kilometers", "feet", and "miles"

    :Outputs: *float* -- The computed pixel spacing
        

.. _pfdf.projection.BoundingBox.transform:

.. py:method:: BoundingBox.transform(self, nrows, ncols)
        
    Returns a Transform object derived from the BoundingBox
    
    ::

        self.transform(nrows, ncols)

    Converts the BoundingBox to a Transform object, given a number of raster rows and columns.
    
    :Inputs:
        * **nrows** (*int*) -- The number of raster rows
        * **ncols** (*int*) -- The number of raster columns

    :Outputs: *Transform* -- A Transform object derived from the BoundingBox
        
----

As Built-In
-----------

.. _pfdf.projection.BoundingBox.tolist:

.. py:method:: BoundingBox.tolist(self, crs = True)

    Returns a BoundingBox as a list

    ::

        self.tolist()
        self.tolist(crs=False)

    Returns the current BoundingBox as a list. By default, the list will have 5 elements. The first four elements are left, bottom, right, and top (in that order). The fifth element is the CRS information. Set crs=False to exclude the CRS information and return a list with only 4 elements.

    :Inputs:
        * **crs** (*bool*) -- True (default) to return CRS information as the 5th element. False to exclude CRS information and return a list with 4 elements.

    :Outputs: *list* -- The BoundingBox as a list

.. _pfdf.projection.BoundingBox.todict:

.. py:method:: BoundingBox.todict(self)

    Returns a BoundingBox as a dict

    ::
      
        self.todict()

    Returns the BoundingBox as a dict. The dict will have 5 keys. The first four are "left", "bottom", "right", and "top" and hold the coordinates of the box's edges. The 5th key is "crs" and holds the associated CRS information.

    :Outputs: *dict* -- The BoundingBox as a dict


----

Testing
-------

.. _pfdf.projection.BoundingBox.isclose:

.. py:method:: BoundingBox.isclose(self, other, rtol = 1e-5, atol = 1e-8)

    True if two BoundingBox objects are similar

    .. dropdown:: Test Similarity

        ::
        
            self.isclose(other)

        Tests if another BoundingBox object has similar values to the current object. Compares both the CRSs and the edge coordinates. Uses numpy.allclose to compare the 4 edge coordinates. True if numpy.allclose return True AND the two objects have compatible CRSs. (Two CRSs are compatible if the two CRSs are equal, or at least one CRS is None).

    .. dropdown:: Set Tolerance

        ::

            self.isclose(..., rtol, atol)

        Specify the relative tolerance and absolute tolerance for the numpy.allclose check. By default, uses a relative tolerance of 1E-5, and an absolute tolerance of 1E-8.

    :Inputs:
        * **other** (*Transform*) -- Another BoundingBox object
        * **rtol** (*scalar*) -- The relative tolerance for float comparison. Defaults to 1E-5.
        * **atol** (*scalar*) -- The absolute tolerance for float comparison. Defaults to 1E-8

    :Outputs: *bool* -- True if the other BoundingBox is similar to the current object


