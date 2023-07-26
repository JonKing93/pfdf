"""
_rasters  Internal processing of raster datasets
----------
This module contains utilities to help manage raster datasets internally within
the package. In particular, the module defines the "Raster" class, which stores a
raster dataset and its metadata values. Use the "Raster.validate" command to validate
a user-provided raster and return it as a Raster object. This object is then
suitable for internal processing.

The Raster class is private, so should not be exposed to users. User-facing type
hints should not reference these objects, and user-facing functions should not
return Raster objects as output. You can use the "output" function to return a
computed raster array in a form suitable for users, and see also the IO methods
of the Raster class for additional options.
----------
Classes:
    Raster      - Internal representation of raster datasets
"""

from pathlib import Path
from typing import Any, Optional, Union
from warnings import catch_warnings, simplefilter

import numpy as np
import rasterio

from pfdf import _validate as validate
from pfdf import rasters
from pfdf._utils import real
from pfdf.rasters import RasterOutput
from pfdf.typing import OutputPath, RasterArray, nodata, shape2d


class Raster:
    """
    Raster  Internal representation of raster datasets
    ----------
    The Raster class is used to pass raster datasets internally through the pfdf
    package. The class includes properties for data access (the Path to a raster
    file, in-memory data values), as well as raster metadata. The class provides
    methods for raster IO and additionally tracks whether a raster is loaded into
    memory to minimize file reads.

    Note that this class is strictly intended for internal use, as all properties
    have read-write access. As such, Raster objects should not appear in user-facing
    type hints, and should not be returned as output from user-facing functions.
    Either return the Raster path, or see the "as_user_raster" method to return the
    raster as a user-facing rasters.Raster object.

    Also, it is always best to use validated Rasters for internal processing.
    As such, the recommended way to obtain a Raster object for a user-provided
    raster is by calling Raster.validate (rather than calling the Raster constructor
    directly). But the constructor is fine for rasters computed internally by
    the package.

    Finally, note that setting the ".values" property directly has additional
    requirements/consequences. First, the new "values" array must match the
    dtype of the object (i.e. dtype cannot change). Setting the values will also
    change the path to None, and will also update the shape. Note that if you
    *do* want to change the dtype of the values, you must first set the dtype
    explicitly to the new type, then change the values.
    ----------
    PROPERTIES:
    Data:
        path            - The path to a file-based raster
        values          - The data values in the raster. None if not loaded

    Metadata:
        shape           - The 2D shape of the raster (nRows, nCols)
        dtype           - The numpy dtype of the raster
        nodata          - The NoData value

    Internal:
        _values         - The saved data values

    METHODS:
    Object Creation:
        __init__        - Creates a new Raster object
        _from_file       - Initializes object from a file-based raster
        _from_array      - Initializes object from a numpy array
        _from_raster     - Initializes object from a rasters.Raster object

    File IO:
        load            - Loads raster values into memory. (Does nothing if already loaded)
        save            - Saves raster values to a GeoTIFF

    User IO:
        validate        - Validates a user-provided raster and returns as a Raster object
        output          - Returns a computed numpy array or pysheds Raster as user-facing output

    Conversions:
        as_user_raster  - Returns the raster as a rasters.Raster object
        as_input        - Returns raster in a form suitable as a dem module function input
    """

    #####
    # Object Creation
    #####

    def __init__(
        self, raster: Union[Path, np.ndarray, rasters.Raster], load: bool = True
    ) -> None:
        """
        __init__  Creates a new Raster object
        ----------
        Raster(raster)
        Creates a Raster object from a Path, numpy array, or rasters.Raster object.
        If the input raster is a Path, loads its data values into memory.

        Raster(raster, load=False)
        Creates a Raster object, but does not load file-based raster values
        into memory. See the "load" method to load values at a later point. Note
        that this option has no effect on numpy arrays and rasters.Raster objects.
        ----------
        Inputs:
            raster: The raster dataset
            load: True (default) to load file-based rasters into memory. False
                to not load.

        Outputs:
            Raster: The Raster object for the dataset
        """

        # Initialize properties
        self.path = None
        self._values = None
        self.shape = None
        self.dtype = None
        self.nodata = None

        # Build object
        if isinstance(raster, Path):
            self._from_file(raster)
        elif isinstance(raster, np.ndarray):
            self._from_array(raster)
        elif isinstance(raster, rasters.Raster):
            self._from_raster(raster)

        # Optionally load file-based rasters
        if load:
            self.load()

    def _from_file(self, path: Path) -> None:
        "Initializes object from a file-based raster"

        # Record path. Always read the first band
        self.path = path
        band = 1

        # Suppress georeferencing warnings
        with catch_warnings():
            simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)

            # Open file and get metadata
            with rasterio.open(path) as file:
                self.shape = (file.height, file.width)
                self.dtype = file.dtypes[band - 1]
                self.nodata = file.nodata

    def _from_array(self, array: np.ndarray) -> None:
        "Initializes object from a numpy array"

        self._values = array
        self.shape = array.shape
        self.dtype = array.dtype

    def _from_raster(self, raster: rasters.Raster) -> None:
        "Initializes objects from a rasters.Raster"

        self._from_array(raster.array)
        self.nodata = raster.nodata

    #####
    # Data values
    #####

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, values):
        # Require same dtype
        if values.dtype != self.dtype:
            raise RuntimeError(
                "The new values would change the dtype of the Raster object"
            )

        # Update values, path, and shape
        self._values = values
        self.path = None
        self.shape = values.shape

    #####
    # File IO
    #####

    def load(self) -> None:
        """
        load  Loads Raster values into memory
        ----------
        self.load()
        Loads raster values into memory. Does nothing if the raster values are
        already in memory. Otherwise, reads values from band 1 of a raster file.
        ----------
        Notes:
            Loads raster into ".values" property
        """
        band = 1
        if self.values is None:
            with catch_warnings():
                simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
                with rasterio.open(self.path) as file:
                    self._values = file.read(band)

    def save(self, path: Path) -> None:
        """
        save  Saves raster values to a GeoTIFF file
        ----------
        self.save(path)
        Saves raster values to a GeoTIFF file at the specified path. If the raster
        values are a boolean dtype, converts to int8 before saving. Raises a
        RuntimeError if the raster values are not in memory.
        ----------
        Inputs:
            path: The Path to the output GeoTIFF file.

        Saves:
            A GeoTIFF file matching the "path" input.
        """

        # Ensure values are loaded.
        if self.values is None:
            raise RuntimeError(
                f"Cannot save raster to:\n\t{path}\nbecause the raster values have "
                "not been loaded into memory."
            )

        # Rasterio does not accept boolean dtype, so convert to int8 first
        if self.dtype == bool:
            dtype = "int8"
        else:
            dtype = self.dtype

        # Temporarily disable the NotGeoreferencedWarning. This should eventually be
        # replaced with functionality for crs and transform options.
        with catch_warnings():
            simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)

            # Save the raster
            band = 1
            with rasterio.open(
                path,
                "w",
                driver="GTiff",
                height=self.shape[0],
                width=self.shape[1],
                count=1,
                dtype=dtype,
                nodata=self.nodata,
            ) as file:
                file.write(self.values, band)

    #####
    # User IO
    #####

    @staticmethod
    def validate(
        raster: Any,
        name: str,
        *,
        shape: Optional[shape2d] = None,
        load: bool = True,
    ) -> "Raster":
        """
        validate  Check input is valid raster and return as Raster object
        ----------
        validate(raster, name)
        Checks that the input is a valid raster. Valid rasters may be:

            * A string with the path to a raster file path,
            * A pathlib.Path to a raster file,
            * An open rasterio.DatasetReader object, or
            * A numpy 2D array with real-valued dtype
            * A rasters.Raster object

        Returns the raster as a Raster object. If the input is not a numpy array or
        rasters.Raster, then the function will read the raster from file. Rasters will
        always be read from band 1.

        Raises exceptions if:
            * a raster file does not exist
            * a raster file cannot be opened by rasterio
            * a numpy array does not have 2 dimensions
            * a numpy array dtype is not an integer, floating, or boolean dtype
            * the input is some other type

        validated(..., *, shape)
        Require the raster to have the specified shape. Raises a ShapeError if this
        condition is not met.

        validated(..., *, load=False)
        Indicates that file-based rasters (those derived from a string, pathlib.Path,
        or rasterio.DatasetReader object) should not be loaded into memory after
        validating. If the input was a file-based raster, returns a pathlib.Path
        object for the validated raster file instead of a numpy array. Input numpy
        arrays are not affected and still return a numpy array.
        ----------
        Inputs:
            raster: The input being checked
            name: The name of the input for use in error messages
            shape: (Optional) A required shape for the raster. A 2-tuple, first
                element is rows, second element is columns. If an element is -1,
                disables shape checking for that axis.
            load: True (default) if validated file-based rasters should be loaded
                into memory and returned as a numpy array. If False, returns a
                pathlib.Path object for file-based rasters.

        Outputs:
            Raster: The validated Raster
        """

        # Convert string to Path
        if isinstance(raster, str):
            raster = Path(raster)

        # If Path, require file exists
        if isinstance(raster, Path):
            raster = raster.resolve(strict=True)

        # If DatasetReader, check that the associated file exists. Get the
        # associated Path to allow loading within a context manager without closing
        # the user's object
        elif isinstance(raster, rasterio.DatasetReader):
            raster = Path(raster.name)
            if not raster.exists():
                raise FileNotFoundError(
                    f"The raster file associated with the input rasterio.DatasetReader "
                    f"object no longer exists.\nFile: {raster}"
                )

        # Otherwise, must be a numpy array or UserRaster object
        elif not isinstance(raster, (np.ndarray, rasters.Raster)):
            raise TypeError(
                f"{name} is not a recognized raster type. Allowed types are: "
                "str, pathlib.Path, rasterio.DatasetReader, "
                "2D numpy.ndarray, and rasters.Raster objects"
            )

        # Initialize Raster object
        raster = Raster(raster, load)

        # Validate
        if raster.path is None:
            raster.values = validate.matrix(raster.values, name)
        validate.dtype_(name, allowed=real, actual=raster.dtype)
        if shape is not None:
            validate.shape_(
                name, ["rows", "columns"], required=shape, actual=raster.shape
            )
        return raster

    @staticmethod
    def output(
        raster: RasterArray, path: OutputPath, nodata: nodata = None
    ) -> RasterOutput:
        """Returns a numpy array in a form suitable as user output.
        If a path is specified, saves the raster and returns the path. Otherwise,
        returns the raster as a UserRaster object. Optionally sets a NoData value."""

        raster = Raster(raster)
        raster.nodata = nodata
        if path is None:
            return raster.as_user_raster()
        else:
            raster.save(path)
            return path

    #####
    # Conversions
    #####
    def as_user_raster(self) -> rasters.Raster:
        """Returns the raster as a rasters.Raster object."""
        self.load()
        return rasters.Raster(self.values, nodata=self.nodata)

    def as_input(self) -> RasterOutput:
        "Returns raster in a form suitable as a dem module function input"
        if self.path is None:
            return self.as_user_raster()
        else:
            return self.path
