utils.nodata module
===================

.. _pfdf.utils.nodata:

.. py:module:: pfdf.utils.nodata

    Utility functions for working with NoData values.

    .. list-table::
        :header-rows: 1

        * - Function
          - Description
        * - :ref:`default <pfdf.utils.nodata.default>`
          - Returns the default NoData value for a dtype
        * - :ref:`mask <pfdf.utils.nodata.mask>`
          - Returns the NoData mask or data mask for an array

.. _pfdf.utils.nodata.default:

.. py:function:: default(dtype)

    Returns the default NoData value for a numpy dtype

    ::
    
        default(dtype)

    Returns the default NoData value for the queried dtype. Returns NaN for floats, the lower bound for signed integers, upper bound for unsigned integers, False for bool, and None for anything else.

    :Inputs:
        * **dtype** (*dtype*) -- The dtype whose default NoData should be returned

    :Outputs: 
        *nan | int | False | None* -- The default NoData value for the dtype




.. _pfdf.utils.nodata.mask:

.. py:function:: mask(array, nodata, invert = False)

    Returns the NoData mask or data mask for an array

    .. dropdown:: NoData Mask

        ::

            mask(array, nodata)

        Returns the NoData mask for the array. The mask will be a boolean array with the same shape as the input array. True elements indicate NoData values, and False elements indicate data elements.

    .. dropdown:: Data Mask

        ::

           mask(array, nodata, invert=True)

        Returns the data mask for the array. True elements indicate data values, and False elements indicate NoData values.

    :Inputs:
        * **array** (*ndarray*) -- The array whose mask should be returned
        * **nodata** (*scalar*) -- The nodata value for the array
        * **invert** (*bool*) -- True to return the data mask for the array. False (default) to
            return the NoData mask.

    :Outputs:
        *boolean numpy array* -- The NoData or data mask for the array


