Input Arrays
============

Many pfdf commands require one or more numeric arguments as input. The library ultimately converts these inputs to numpy arrays, but pfdf is flexible enough to accept a variety of input types. Here, we distinguish between scalar, vector, and matrix inputs.

Scalars
-------
A scalar input has a single data element. The following values are all acceptable scalars::

    >>> import numpy as np

    # Numpy scalars, or arrays with a single element
    >>> np.array(5)
    >>> np.array(5).reshape(1)
    >>> np.array(5).reshape(1,1,1,1,1,1,1)

    # int or float
    >>> 5
    >>> 5.0

    # List or tuple with a single element
    >>> [5]
    >>> (5,)

Vectors
-------
A vector is a 1D array of data values. In the context of pfdf, a vector input may have any number of dimensions, but only one dimension may be non-singleton (have a length greater than 1). The following values are all acceptable vectors::

    >>> import numpy as np

    # All scalars
    >>> np.array(5)
    >>> 5
    >>> [5]
    # etc.

    # Numpy arrays with one non-singleton dimension
    >>> np.arange(5)
    >>> np.arange(5).reshape(1,1,1,1,5,1,1)

    # List or tuple of ints/floats
    >>> [1,2,3.3,4,5.5]
    >>> (1,2,3.3,4,5.5)


Matrices
--------
A matrix is a 2D array of data values. In the context of pfdf, most matrices are handled via the :doc:`Raster class <rasters/intro>`. However, when this is not the case, a matrix should be an array in which only the first two dimensions may be non-singleton. The following values are acceptable matrices::

    >>> import numpy as np

    # All scalars and most vectors
    >>> 5
    >>> [5, 6, 7]
    >>> np.arange(5)
    # etc.

    # Only dimensions<2 are non-singleton
    >>> np.arange(10).reshape(10,1)
    >>> np.arange(10).reshape(5,2)
    >>> np.arange(10).resshape(5,2,1,1,1,1,1)
