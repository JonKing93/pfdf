NoData Utilities
================

The :ref:`utils.nodata module <pfdf.utils.nodata>` provides two utility functions for working with NoData values.

.. _default-nodata:

Default NoData
--------------
By default, *Raster* objects try to ensure they have a NoData value. So if you create a *Raster* object from a dataset that lacks a NoData value (for example, from a raw numpy array), then the object will assign a default NoData value based on the raster's dtype. Default values are assigned as follows:

.. list-table::
    :header-rows: 1

    * - Dtype
      - Default NoData
    * - Float
      - nan
    * - Signed integer
      - Lowest represetable value
    * - Unsigned integer
      - Highest representable value
    * - bool
      - False
    * - Anything else
      - None

You can use the :ref:`nodata.default function <pfdf.utils.nodata.default>` to query the default value for specific dtypes:

.. code:: pycon

    >>> from pfdf.utils import nodata

    >>> nodata.default('float32')
    nan
    >>> nodata.default('int64')
    -9223372036854775808
    >>> nodata.default('int16')
    -32768
    >>> nodata.default('uint16')
    65535
    >>> nodata.default(bool)
    False


Data Mask
---------

.. tip::

    It is usually preferable to use the :ref:`Raster.data_mask <pfdf.raster.Raster.data_mask>` or :ref:`Raster.nodata_mask <pfdf.raster.Raster.nodata_mask>` properties, rather than this function.

The :ref:`mask function <pfdf.utils.nodata.mask>` returns a NoData mask or data mask, given an array and a NoData value. In a NoData mask, NoData elements are marked as True:

.. code:: pycon

    >>> from pfdf.utils import nodata
    >>> nodata.mask([1,2,3], nodata=2)
    array([False,  True, False])

A data mask is the opposite - data elements are marked as True. Use the "invert" option to return a data mask instead:

.. code:: pycon

    >>> nodata.mask([1,2,3], invert=True)
    array([ True, False,  True])