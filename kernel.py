"""
kernel  Functions involved in building kernel files for confinement analysis
----------
The kernel module is used to build the kernel files for confinement analysis.
These kernel files are used to implement irregular focal statistics in ArcPy.
----------
Key Functions:
    build   - Builds all kernel files for a kernel of given size

Utility Functions:
    write   - Writes a single kernel file
    string  - Converts a kernel array to string
    vector  - Returns a specified kernel vector
    matrix  - Returns a specified kernel matrix
    zeros   - Returns the indices of kernel elements that should be converted to zeros
"""

from math import floor
from numpy import ones, identity, rot90
from os import getcwd, path

def build(N, directory=None):
    """
    kernel.build  Build all kernel files for a kernel of given size
    ----------
    files = kernel.build(N)
    Builds kernel files for a kernel of given size in the current directory.
    Builds files for the left, right, up, down, upleft, downright, downleft, and
    upright directions. The kernel file for each direction follows the naming
    convection "{direction}_{N}x{N}.txt". Returns a dictionary whose keys are
    the different directions. The value for each key is the full name of the
    associated kernel file.

    files = kernel.build(N, directory)
    Builds the kernel files in the specified directory. Raises a ValueError if
    the directory does not exist.
    ----------
    Inputs:
        N (int): The size of the kernel. Should be odd.
        directory (str): The path of an existing directory in which to build
            the kernel files.

    Outputs:
        files (dict): Holds the full path of the kernel file for each direction.
            Keys are the kernel directions: left, right, up, down, upleft,
            downright, downleft, and upright.
    """

    # Default path is current directory. Otherwise, get absolute path
    if directory is None:
        directory = getcwd()

    # Otherwise, get absolute path and check directory exists
    else:
        directory = path.abspath(directory)
        if not path.isdir(directory):
            raise ValueError(f"The kernel directory does not exist.\n\tDirectory: {directory}")

    # Locate the center of the neighborhood
    center = floor(N/2)

    # Settings for different kernels
    types = ["left","right","up","down","upleft","downright","downleft","upright"]
    methods = [vector]*4 + [matrix]*4
    isalternate = [False, False, True, True] * 2
    zeros_first = [False, True] * 4

    # Initialize a dict for each kernel file
    files = {type: None for type in types}

    # Get each kernel array and write to file. Add files to the output dictionary
    for (type, method, isaltered, zero_first) in zip(types, methods, isalternate, zeros_first):
        kernel = method(N, center, isaltered, zero_first)
        files[type] = write(directory, type, N, kernel)
    return files

def write(directory, type, N, kernel):
    """
    kernel.write  Writes a single kernel file
    ----------
    filepath = kernel.write(directory, type, N, kernel)
    Writes the file for a given kernel to the specified folder. The file name
    will follow the convention {type}_{N}x{N}.txt.
    ----------
    Inputs:
        directory (str): The path of the folder in which to write the kernel file
        type (str): Indicates the type of kernel file. Forms the first part of
            the kernel file name.
        N (int): The kernel size. Used to form the second part of the kernel
            file name.
        kernel (2D int ndarray): The kernel array to write to file

    Outputs:
        filepath (str): The full path to the written file
    """

    # Get the kernel shape and convert to string
    (nRows, nCols) = kernel.shape
    kernel = string(kernel)

    # Get the file name
    file = f"{type}_{N}x{N}.txt"
    filepath = path.join(directory, file)

    # Write the file contents
    contents = f"{nCols} {nRows}\n{kernel}"
    with open(file, 'w') as file:
        file.write(contents)

    # Return the file name
    return filepath

def string(kernel):
    """
    kernel.string  Convert a kernel array to string
    ----------
    kernel = kernel.string(kernel)
    Converts a kernel ndarray to a string for file writing.
    ----------
    Inputs:
        kernel (ndarray): A kernel array

    Outputs:
        kernel (str): A kernel string for file writing
    """

    kernel = str(kernel)
    kernel = kernel.replace("[","")
    kernel = kernel.replace("]","")
    kernel = kernel.replace("\n ","\n")
    return kernel

def vector(N, center, iscolumn, zeros_first):
    """
    kernel.vector  Return a kernel vector
    ----------
    kernel = kernel.vector(N, center, iscolumn, zeros_first)
    Returns a kernel vector given the kernel size and index of the centering
    element. The kernel vector will either be a row vector (with 2 axes) or a
    column vector (with 2 axes) as specified by the "iscolumn" input. If
    zeros_first is True, then the beginning of the vector is converted to zeros.
    If False, then the end of the vector is converted to zeros.
    ----------
    Inputs:
        N (int): The size of the kernel
        center (int): The index of the centering element
        iscolumn (bool): Set to True to return a column vector. Set to False to
            return a row vector.
        zeros_first (bool): Set to True to convert the beginning of the vector
            to zeros. Set to False to convert the end to zeros.

    Outputs:
        kernel (int ndarray [N x 1] | [1 x N]): The kernel vector. An int
            ndarray that will always have 2 axes.
    """

    # Get the initial row vector of ones
    kernel = ones((1,N), dtype=int)

    # Change elements to zero
    indices = zeros(N, center, zeros_first)
    kernel[0,indices] = 0

    # Adjust shape if vertical
    if iscolumn:
        kernel.shape = (N,1)
    return kernel

def matrix(N, center, isexchange, zeros_first):
    """
    kernel.matrix  Return a kernel matrix
    ----------
    kernel = kernel.matrix(N, center, isexchange, zeros_first)
    Returns a kernel matrix given the kernel size and the index of the centering
    element. The kernel matrix is derived from an identity or exchange matrix,
    as specified by the "isexchange" input. If zeros_first is True, then the
    left side of the matrix will be converted to zeros. If False, then the right
    side of the matrix is converted to zeros.
    ----------
    Inputs:
        N (int): The size of the kernel
        center (int): The index of the centering row/column
        isexchange (bool): False if the output matrix should be derived from an
            identity matrix. True if the output should be derived from an
            exchange matrix.
        zeros_first (bool): True if zeros should be added to the left side of
            the matrix. False to add zeros to the right side.

    Outputs:
        kernel (int ndarray [N x N]): The kernel matrix
    """

    # Get the initial identity matrix
    kernel = identity(N, dtype=int)

    # Change elements to zero
    indices = zeros(N, center, zeros_first)
    kernel[indices, indices] = 0

    # Rotate if an exchange matrix
    if isexchange:
        kernel = rot90(kernel)
    return kernel

def zeros(N, center, zeros_first):
    """
    kernel.zeros  Returns the indices of kernel elements that should be converted to zeros
    ----------
    indices = kernel.zeros(N, center, zeros_first)
    Given a kernel size and centering element, returns the indices of the kernel
    elements that should be converted to 0s. If zeros_first is True, the indices
    will include elements up to and including the center. If zeros_first is
    False, returns indices from the center to end.
    ----------
    Inputs:
        N (int): The size of the kernel neighborhood
        center (int): The index of the centering element in the kernel
        zeros_first (bool): If True, returns indices up to and including the
            centering element. If False, returns indices from (and including)
            the centering element to the end.

    Outputs:
        indices (range): The indices of kernel elements that should be converted
            to zeros.
    """

    if zeros_first:
        return range(0, center+1)
    else:
        return range(center, N)
