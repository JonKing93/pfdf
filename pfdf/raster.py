"""
raster  A class and type hint for working with raster datasets
----------
This module provides the "Raster" class, which pfdf uses to manage raster datasets.
The class can acquire raster values and metadata from a variety of raster formats,
and all computed rasters are returned as Raster objects. (And please see the docstring
of the Raster class for additional details). The module also provides the "RasterInput" 
type hint, which denotes all types that pfdf accepts as representing a raster.

Users may be particularly interested in the "Raster.from_array" and "Raster.save"
methods. Raster.from_array allows users to add raster metadata (NoData value, 
affine transform, and CRS) to numpy arrays. Raster.save allows a user to save
an output raster to a GeoTIFF file format.
----------
Class:
    Raster      - Class that manages raster datasets and metadata

Type Hint:
    RasterInput - Types that are convertible to a Raster object
"""

from pathlib import Path
from typing import Any, Optional, Self

import numpy as np
import rasterio
from affine import Affine
from pysheds.sview import Raster as pysheds_raster
from pysheds.sview import ViewFinder
from rasterio.crs import CRS

from pfdf._utils import real, validate
from pfdf.errors import RasterCrsError, RasterShapeError, RasterTransformError
from pfdf.typing import MatrixArray, Pathlike, scalar, shape2d


class Raster:
    """
    Raster  Manages raster datasets and metadata
    ----------
    OVERVIEW:
    The Raster class is used to manage raster datasets and metadata within the pfdf
    package. Use the ".values" property to return the data values for a raster.
    Raster metadata is returned using the following properties: shape, size, dtype,
    nodata, transform, and crs. Users can also return all metadata values in a
    dict using the ".metadata" property. The values and metadata properties are
    read-only, but Raster objects also include a read-write ".name" property,
    which users can use to optionally label a raster dataset.

    INPUT RASTERS:
    The pfdf package uses the Raster class to convert input rasters to a common
    format for internal processing. Currently, the class supports the following
    formats for input rasters: file-based rasters (string, pathlib.Path,
    rasterio.DatasetReader), numpy arrays, pysheds.sview.Raster objects, and
    other pfdf.raster.Raster objects.

    It is usually not necessary to convert raster inputs to Raster object, as
    pfdf handles this conversion automatically. As such, users can provide any
    supported raster format directly to pfdf commands. One caveat is that a raster
    represented by a raw numpy array will not have any associated NoData value,
    affine transformation, or coordinate reference system. However, users can call
    the "Raster.from_array" method to add these metadata values to numpy arrays.

    OUTPUT RASTERS:
    All rasters computed by pfdf are returned as Raster objects. Users can return
    the computed values using the aforementioned ".values" property. See also
    the "save" method to save an output raster to a GeoTIFF file format.
    ----------
    FOR USERS:
    Properties:
        name            - An optional name to identify the raster
        values          - The data values associated with a raster
        shape           - The shape of the raster array
        size            - The size (number of elements) in the raster array
        dtype           - The dtype of the raster array
        nodata          - The NoData value associated with the raster
        transform       - The Affine transformation used to map raster pixels to spatial coordinates
        crs             - The coordinate reference system associated with the raster
        metadata        - A dict with shape, dtype, nodata, transform, and crs metadata

    Object Creation:
        __init__        - Returns a raster object for a supported raster input
        from_array      - Creates a Raster object from a raw numpy array with optional metadata

    IO:
        save            - Saves a raster as a GeoTIFF
        as_pysheds      - Returns a Raster as a pysheds.sview.Raster object

    INTERNAL:
    Attributes:
        _values         - Saved data values
        _nodata         - NoData value
        _transform      - Affine transformation
        _crs            - Coordinate reference system

    Initialization:
        _from_file      - Builds object from a file-based raster
        _from_pysheds   - Builds object from a pysheds.sview.Raster object
        _from_raster    - Builds object from another pfdf.raster.Raster object

    Validation:
        _validate       - Validates an input raster against the current Raster
    """

    #####
    # Properties
    #####

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("raster name must be a string")
        self._name = name

    @property
    def values(self) -> np.ndarray:
        return self._values

    @property
    def shape(self) -> shape2d:
        return self._values.shape

    @property
    def size(self) -> int:
        return self._values.size

    @property
    def dtype(self) -> np.dtype:
        return self._values.dtype

    @property
    def nodata(self) -> scalar:
        return self._nodata

    @property
    def transform(self) -> Affine:
        return self._transform

    @property
    def crs(self) -> CRS:
        return self._crs

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "shape": self.shape,
            "size": self.size,
            "dtype": self.dtype,
            "nodata": self.nodata,
            "transform": self.transform,
            "crs": self.crs,
        }

    # Type hint equivalent to RasterInput, but using "Self" instead of "Raster"
    _RasterInput = (
        Self | str | Path | rasterio.DatasetReader | MatrixArray | pysheds_raster
    )

    #####
    # Object Creation
    #####

    def __init__(
        self,
        raster: _RasterInput,
        name: Optional[str] = None,
    ) -> None:
        """
        __init__  Creates a new Raster object
        ----------
        Raster(raster)
        Returns the input raster as a Raster object. Supports both file-based
        and in-memory raster inputs. File-based rasters may be provided using a
        string, pathlib.Path, or rasterio.DatasetReader for the file. Otherwise,
        the raster input should be a numpy.ndarray, pysheds.sview.Raster object,
        or another Raster object. The input raster should refer to a 2D array with
        a boolean, integer, or floating dtype - raises Exceptions when this is not
        the case.

        Note that most users will not need this constructor, as pfdf commands
        accept all supported raster types directly as input. However, the "from_array"
        method may be useful when using raw numpy arrays as rasters.

        Raster(raster, name)
        Optionally specifies a name for the raster. This can be returned using
        the ".name" property, and is used to identify the raster in error messages.
        Defaults to "raster" if unspecified.
        ----------
        Inputs:
            raster: A supported raster dataset
            name: A name for the input raster. Defaults to 'raster'

        Outputs:
            Raster: The Raster object for the dataset

        Raises:
            FileNotFoundError: If a file-based raster cannot be found
            TypeError: If an input raster is not a supported type
        """

        # Set name
        if name is None:
            name = "raster"
        self.name = name

        # Initialize attributes
        self._values: MatrixArray = None
        self._nodata: scalar = None
        self._transform: Affine = None
        self._crs: CRS = None

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

        # Otherwise, must be an array-based object
        elif not isinstance(raster, (np.ndarray, Raster, pysheds_raster)):
            raise TypeError(
                f"{name} is not a recognized type. Allowed types are: "
                "str, pathlib.Path, rasterio.DatasetReader, 2d numpy.ndarray, "
                "pfdf.raster.Raster, and pysheds.sview.Raster objects."
            )

        # Build object and validate matrix
        if isinstance(raster, Path):
            self._from_file(raster)
        elif isinstance(raster, pysheds_raster):
            self._from_pysheds(raster)
        elif isinstance(raster, Raster):
            self._from_raster(raster)
        elif isinstance(raster, np.ndarray):
            self._values = raster

        # Validate array
        self._values = validate.matrix(self._values, name, dtype=real)

    def _from_file(self, path: Path) -> None:
        "Initializes object from band 1 of a file-based raster"
        band = 1
        with rasterio.open(path) as file:
            self._values = file.read(band)
            self._nodata = file.nodata
            self._transform = file.transform
            self._crs = file.crs

    def _from_raster(self, raster: Self) -> None:
        "Initialize object from pfdf.rasters.Raster"
        self._values = raster._values
        self._nodata = raster._nodata
        self._transform = raster._transform
        self._crs = raster._crs

    def _from_pysheds(self, raster: pysheds_raster) -> None:
        "Initialize object from pysheds.sview.Raster"
        self._values = np.array(raster, copy=False)
        self._nodata = raster.nodata
        self._transform = raster.affine
        self._crs = CRS.from_wkt(raster.crs.to_wkt())

    @staticmethod
    def from_array(
        array: MatrixArray,
        *,
        name: Optional[str] = None,
        nodata: Optional[scalar] = None,
        transform: Optional[Affine] = None,
        crs: Optional[CRS] = None,
    ) -> Self:
        """
        from_array  Add raster metadata to a raw numpy array
        ----------
        from_array(array)
        Initializes a Raster object from a raw numpy array. The NoData value,
        transform, and crs for the returned object will all be None.

        from_array(..., *, name)
        from_array(..., *, nodata)
        from_array(..., *, transform)
        from_array(..., *, crs)
        Specify a name, NoData value, transform, and/or coordinate reference
        system (crs) that should be associated with the numpy array dataset. The
        output Raster object will include any specified metadata.

        The raster name can be returned using the ".name" property and is used
        to identify the raster in error messages. Defaults to 'raster' if unset.

        The NoData value will be set to the same dtype as the array. Raises a
        TypeError if the NoData value cannot be safely casted to this dtype.

        The transform specifies the affine transformation used to map pixel indices
        to spatial points, and should be an affine.Affine object. Common ways
        to obtain such an object are using the ".transform" property from rasterio
        and Raster objects, or via the ".affine" property of pysheds rasters.

        The crs is the coordinate reference system used to locate spatial points.
        This should be a rasterio.crs.CRS object. These can be obtained using the
        ".crs" property from rasterio or Raster objects, and see also the rasterio
        documentation for building these objects from formats such as well-known
        text (WKT) and PROJ4 strings.
        ----------
        Inputs:
            array       - A 2D numpy array whose data values represent a raster
            name        - A name for the raster. Defaults to 'raster'
            nodata      - A NoData value for the raster
            transform   - An affine transformation for the raster (affine.Affine)
            crs         - A coordinate reference system for the raster (rasterio.crs.CRS)

        Outputs:
            Raster: A raster object for the array-based raster dataset
        """

        # Build the initial object
        array = np.array(array)
        raster = Raster(array, name)

        # Check metadata values (if provided)
        if nodata is not None:
            raster._nodata = validate.nodata(nodata, raster.dtype)
        if transform is not None:
            raster._transform = validate.transform(transform)
        if crs is not None:
            raster._crs = validate.crs(crs)
        return raster

    #####
    # IO
    #####

    def save(self, path: Pathlike, overwrite: bool = False) -> None:
        """
        save  Save a raster dataset to a GeoTIFF file
        ----------
        self.save(path)
        Saves the current Raster to the indicated path as a GeoTIFF. Raises a
        FileExistsError if the file already exists. Note that boolean rasters
        will be saved as an "int8" dtype to accomodate the GeoTIFF format.

        self.save(path, overwrite=True)
        Allows the saved file to replace an existing file.
        ----------
        Inputs:
            path: The path to the saved output file
            overwrite: False (default) to prevent the output from replacing
                existing file. True to allow replacement.
        """

        # Validate and resolve path
        path = validate.output_path(path, overwrite)

        # Rasterio does not accept boolean dtype, so convert to int8 instead
        if self.dtype == bool:
            dtype = "int8"
        else:
            dtype = self.dtype

        # Save the raster
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=self.shape[0],
            width=self.shape[1],
            count=1,
            dtype=dtype,
            nodata=self.nodata,
            transform=self.transform,
            crs=self.crs,
        ) as file:
            file.write(self._values, 1)

    def as_pysheds(self) -> pysheds_raster:
        """
        as_pysheds  Converts a Raster to a pysheds.sview.Raster object
        ----------
        self.as_pysheds()
        Returns the current Raster object as a pysheds.sview.Raster object. Note
        that the pysheds raster will use default values for any metadata that are
        missing from the Raster object. These default values are as follows:

            nodata: 0
            affine (transform): Affine(1,0,0,0,1,0)
            crs: EPSG 4326

        Please see the documentation on pysheds rasters for additional details on
        using these outputs: https://mattbartos.com/pysheds/raster.html
        ----------
        Outputs:
            pysheds.sview.Raster: The Raster as a pysheds.sview.Raster object
        """

        # Get available metadata
        metadata = {"shape": self.shape}
        if self.nodata is not None:
            metadata["nodata"] = self.nodata
        if self.transform is not None:
            metadata["affine"] = self.transform
        if self.crs is not None:
            metadata["crs"] = self.crs

        # Pysheds crashes when using its default NoData value for boolean rasters,
        # so set this explicitly as a boolean
        if self.dtype == bool:
            if self.nodata is None:
                metadata["nodata"] = False
            else:
                metadata["nodata"] = bool(self.nodata)

        # Initialize viewfinder and build raster.
        view = ViewFinder(**metadata)
        return pysheds_raster(self._values, view)

    def _validate(self, raster: _RasterInput, name: str) -> Self:
        """
        _validate  Validates a second raster and its metadata against the current raster
        ----------
        self._validate(raster, name)
        Validates an input raster against the current Raster object. Checks that
        the second raster's metadata matches the shape, affine transform, and
        crs of the current object. Raises various RasterErrors if these criteria
        are not met. Otherwise, returns the validated raster dataset as a Raster object.
        ----------
        Inputs:
            raster: The input raster being checked
            name: A name for the raster for use in error messages

        Outputs:
            Raster: The validated Raster dataset

        Raises:
            RasterShapeError: If the raster does not have the required shape
            TransformError: If the raster has a different transform
            CrsError: If the raster has a different crs
        """

        raster = Raster(raster, name)
        if raster.shape != self.shape:
            raise RasterShapeError(
                f"The shape of the {raster.name} {raster.shape}, does not "
                f"match the shape of the {self.name} {self.shape}."
            )
        elif raster.transform != self.transform:
            raise RasterTransformError(
                f"The affine transformation of the {raster.name}:\n{raster.transform}\n"
                f"does not match the transform of the {self.name}:\n{self.transform}"
            )
        elif raster.crs != self.crs:
            raise RasterCrsError(
                f"The CRS of the {raster.name} ({raster.crs}) does not "
                f"match the CRS of the {self.name} ({self.crs})."
            )
        return raster


#####
# Type Hints
#####
RasterInput = (
    str | Path | rasterio.DatasetReader | MatrixArray | Raster | pysheds_raster
)
