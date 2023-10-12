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
a raster dataset to file.
----------
Class:
    Raster      - Class that manages raster datasets and metadata

Type Hint:
    RasterInput - Types that are convertible to a Raster object
"""

from math import nan, sqrt
from pathlib import Path
from typing import Any, Optional, Self

import numpy as np
import rasterio
from affine import Affine
from pysheds.sview import Raster as PyshedsRaster
from pysheds.sview import ViewFinder
from rasterio.coords import BoundingBox
from rasterio.crs import CRS

from pfdf._utils import nodata_, real, validate
from pfdf.errors import RasterCrsError, RasterShapeError, RasterTransformError
from pfdf.typing import Casting, MatrixArray, Pathlike, scalar, shape2d


class Raster:
    """
    Raster  Manages raster datasets and metadata
    ----------
    OVERVIEW AND PROPERTIES:
    The Raster class is used to manage raster datasets and metadata within the pfdf
    package. Use the ".values" property to return the data values for a raster.
    The dtype and nodata values return additional information about the data
    values. Information about the array shape is available via the shape, size,
    height, and width properties.

    A number of properties provide spatial information about the raster. The crs
    property reports the coordinate reference system associated with the raster,
    and .transform reports the (affine) transformation matrix used to convert
    pixel indices to spatial coordinates. The bounds property returns a rasterio
    BoundingBox object that reports the spatial coordinates of the raster's corners.

    Several other properties describe the pixels in the raster. The "resolution"
    property reports the X-axis and Y-axis spacing between raster pixels. The
    pixel_area property reports the area of a single pixel, and pixel_diagonal
    reports the length across the diagonal of a single pixel.

    Note that the (affine) transform may only support scaling and translation.
    That is, the b and d coefficients of the transformation matrix must be 0.
    Also, the bounds, resolution, pixel_area, and pixel_diagonal properties are
    derived from the transform, so will return NaN values if the raster has no
    transform.

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

    Some pfdf commands require multiple rasters as input. When this is the case,
    the various rasters are usually required to have the same shape, crs, and
    transform as the first input raster (the primary raster). If a secondary
    raster does not have a CRS or transform, these values are assumed to match the
    primary raster. So you can use georeferenced raster and a numpy array as a
    primary and secondary raster - for example, a georeferenced raster of data
    values and a boolean data mask.

    OUTPUT RASTERS:
    All rasters computed by pfdf are returned as Raster objects. Users can return
    the computed values using the aforementioned ".values" property. See also
    the "save" method to save an output raster to various file formats.

    Note that the ".values" method returns a read-only view of the raster's
    data values. If you need to edit the values, you should first make an editable
    copy. Raster values are numpy arrays, so you can make a copy using their ".copy"
    method. For example:
        >>> editable_values = my_raster.values.copy()
    ----------
    FOR USERS:
    Object Creation:
        __init__        - Returns a raster object for a supported raster input
        from_array      - Creates a Raster object from a raw numpy array with optional metadata
        copy            - Returns a copy of the current Raster object

    Data Properties:
        name            - An optional name to identify the raster
        values          - The data values associated with a raster
        dtype           - The dtype of the raster array
        nodata          - The NoData value associated with the raster

    Shape Properties:
        shape           - The shape of the raster array
        size            - The size (number of elements) in the raster array
        height          - The number of rows in the raster array
        width           - The number of columns in the raster array

    Spatial Properties:
        crs             - The coordinate reference system associated with the raster
        transform       - The Affine transformation used to map raster pixels to spatial coordinates
        bounds          - A BoundingBox with the spatial coordinates of the raster's corners

    Pixel Properties:
        resolution      - The spacing of raster pixels along the X and Y axes in the units of the transform
        pixel_area      - The area of a raster pixel in the units of the transform squared
        pixel_diagonal  - The length of the diagonal of a raster pixel in the units of the transform

    IO:
        save            - Saves a raster dataset to file
        as_pysheds      - Returns a Raster as a pysheds.sview.Raster object

    Dunders:
        __eq__          - True if the second object is a Raster with the same values, nodata, transform, and crs

    INTERNAL:
    Attributes:
        _name               - Identifying name
        _values             - Saved data values
        _nodata             - NoData value
        _crs                - Coordinate reference system
        _transform          - Affine transformation

    Initialization:
        _from_file          - Builds object from a file-based raster
        _from_pysheds       - Builds object from a pysheds.sview.Raster object
        _from_raster        - Builds object from another pfdf.raster.Raster object

    Validation:
        _validate           - Validates an input raster against the current Raster
        _validate_metadata  - Validates crs, transform, and NoData values
    """

    #####
    # Properties
    #####

    ##### Data

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
        return self._values.view()

    @property
    def dtype(self) -> np.dtype:
        return self._values.dtype

    @property
    def nodata(self) -> scalar:
        return self._nodata

    ##### Shape

    @property
    def shape(self) -> shape2d:
        return self._values.shape

    @property
    def size(self) -> int:
        return self._values.size

    @property
    def height(self) -> int:
        return self._values.shape[0]

    @property
    def width(self) -> int:
        return self._values.shape[1]

    ##### Spatial

    @property
    def crs(self) -> CRS:
        return self._crs

    @property
    def transform(self) -> Affine:
        return self._transform

    @property
    def bounds(self) -> BoundingBox:
        if self.transform is None:
            return BoundingBox(nan, nan, nan, nan)
        else:
            left, top = self.transform * (0, 0)
            right, bottom = self.transform * self.shape
            return BoundingBox(left, bottom, right, top)

    ##### Pixels

    @property
    def resolution(self) -> tuple[float, float]:
        if self.transform is None:
            return (nan, nan)
        else:
            dx = abs(self._transform[0])
            dy = abs(self.transform[4])
            return (dx, dy)

    @property
    def pixel_area(self) -> float:
        dx, dy = self.resolution
        return dx * dy

    @property
    def pixel_diagonal(self) -> float:
        dx, dy = self.resolution
        return sqrt(dx**2 + dy**2)

    # Type hint equivalent to RasterInput, but using "Self" instead of "Raster"
    _RasterInput = (
        Self | str | Path | rasterio.DatasetReader | MatrixArray | PyshedsRaster
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

        # Initialize attributes
        self._name: str = None
        self._values: MatrixArray = None
        self._nodata: scalar = None
        self._crs: CRS = None
        self._transform: Affine = None

        # Set name
        if name is None:
            name = "raster"
        self.name = name

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
        elif not isinstance(raster, (np.ndarray, Raster, PyshedsRaster)):
            raise TypeError(
                f"{name} is not a recognized type. Allowed types are: "
                "str, pathlib.Path, rasterio.DatasetReader, 2d numpy.ndarray, "
                "pfdf.raster.Raster, and pysheds.sview.Raster objects."
            )

        # Build object and validate matrix
        if isinstance(raster, Path):
            self._from_file(raster)
        elif isinstance(raster, PyshedsRaster):
            self._from_pysheds(raster)
        elif isinstance(raster, Raster):
            self._from_raster(raster)
        elif isinstance(raster, np.ndarray):
            self._values = raster.copy()

        # Validate array values and metadata
        self._values = validate.matrix(self._values, name, dtype=real)
        self._validate_metadata(
            self._crs, self._transform, self._nodata, casting="unsafe"
        )

        # Lock the array values. This allows us to return views of the data values
        # (instead of copies) while preventing users from altering the base array
        self._values.setflags(write=False)

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

    def _from_pysheds(self, raster: PyshedsRaster) -> None:
        "Initialize object from pysheds.sview.Raster"
        self._values = np.array(raster, copy=True)
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
        spatial: Optional[Self] = None,
        casting: Casting = "safe",
    ) -> Self:
        """
        from_array  Add raster metadata to a raw numpy array
        ----------
        Raster.from_array(array)
        Initializes a Raster object from a raw numpy array. The NoData value,
        transform, and crs for the returned object will all be None.

        Raster.from_array(..., *, name)
        Raster.from_array(..., *, nodata)
        Raster.from_array(..., *, transform)
        Raster.from_array(..., *, crs)
        Specify a name, NoData value, transform, and/or coordinate reference
        system (crs) that should be associated with the numpy array dataset. The
        output Raster object will include any specified metadata.

        The raster name can be returned using the ".name" property and is used
        to identify the raster in error messages. Defaults to 'raster' if unset.

        The NoData value will be set to the same dtype as the array. Raises a
        TypeError if the NoData value cannot be safely casted to this dtype. See
        below for an option to change the casting requirements for NoData values.

        The transform specifies the affine transformation used to map pixel indices
        to spatial points, and should be an affine.Affine object. Common ways
        to obtain such an object are using the ".transform" property from rasterio
        and Raster objects, or via the ".affine" property of pysheds rasters.

        The crs is the coordinate reference system used to locate spatial points.
        This input should a rasterio.crs.CRS object, or convertible to such an
        object. CRS objects can be obtained using the ".crs" property from rasterio
        or Raster objects, and see also the rasterio documentation for building
        these objects from formats such as well-known text (WKT) and PROJ4 strings.

        Raster.from_array(..., *, spatial)
        Specifies a Raster object to use as a default spatial metadata template.
        By default, transform and crs properties from the template will be copied
        to the new raster. However, these default values can still be overridden
        by providing the transform, and/or crs inputs as usual. In this case, any
        metadata provided by a keyword option will be prioritized over the template
        metadata.

        Raster.from_array(..., *, casting)
        Specifies the type of data casting that may occur when converting a NoData
        value to the dtype of the Raster. Options are as follows:
            'no': The data type should not be cast at all
            'equiv': Only byte-order changes are allowed
            'safe': Only casts which can preserve values are allowed
            'same_kind': Only safe casts or casts within a kind (like float64 to float32)
            'unsafe': Any data conversions may be done
        The default behavior is to require safe casting.
        ----------
        Inputs:
            array: A 2D numpy array whose data values represent a raster
            name: A name for the raster. Defaults to 'raster'
            nodata: A NoData value for the raster
            transform: An affine transformation for the raster (affine.Affine)
            crs: A coordinate reference system for the raster (rasterio.crs.CRS)
            spatial: A Raster object to use as a default spatial metadata template
                for the new Raster.
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".

        Outputs:
            Raster: A raster object for the array-based raster dataset
        """

        # Validate options
        if spatial is not None and not isinstance(spatial, Raster):
            raise TypeError("spatial template must be a pfdf.raster.Raster object")
        casting = validate.option(
            casting, "casting", allowed=["no", "equiv", "safe", "same_kind", "unsafe"]
        )

        # Build the initial object
        array = np.array(array, copy=False)
        raster = Raster(array, name)

        # Parse spatial metadata from template and keyword options
        if spatial is not None:
            if transform is None:
                transform = spatial.transform
            if crs is None:
                crs = spatial.crs

        # Check metadata values (if provided) and return Raster
        raster._validate_metadata(crs, transform, nodata, casting)
        return raster

    def copy(self) -> Self:
        """
        copy  Returns a copy of the current Raster
        ----------
        self.copy()
        Returns a copy of the current Raster. Note that data values are not duplicated
        in memory when copying a raster. Instead, both Rasters reference the same
        underlying array.
        ----------
        Outputs:
            Raster: A Raster with the same data values and metadata as the
                current Raster
        """

        copy = super().__new__(Raster)
        copy._name = self._name
        copy._values = self._values
        copy._nodata = self._nodata
        copy._crs = self._crs
        copy._transform = self._transform
        return copy

    #####
    # Dunders
    #####

    def __eq__(self, other: Any) -> bool:
        """
        __eq__  Test Raster objects for equality
        ----------
        self == other
        True if the other input is a Raster with the same values, nodata, transform,
        and crs. Note that NaN values are interpreted as NoData, and so compare
        as equal. Also note that the rasters are not required to have the same
        name to test as equal.
        ----------
        Inputs:
            other: A second input being compared to the Raster object

        Outputs:
            bool: True if the second input is a Raster with the same values,
                nodata, transform, and crs. Otherwise False
        """

        if (
            isinstance(other, Raster)
            and nodata_.equal(self.nodata, other.nodata)
            and self.transform == other.transform
            and self.crs == other.crs
            and np.array_equal(self.values, other.values, equal_nan=True)
        ):
            return True
        else:
            return False

    #####
    # Validation
    #####

    def _validate_metadata(
        self, crs: Any, transform: Any, nodata: Any, casting: Casting
    ) -> None:
        "Checks that metadata values are valid. If so, sets attributes"

        if crs is not None:
            self._crs = validate.crs(crs)
        if transform is not None:
            self._transform = validate.transform(transform)
        if nodata is not None:
            self._nodata = validate.nodata(nodata, self.dtype, casting)

    def _validate(self, raster: _RasterInput, name: str) -> Self:
        """
        _validate  Validates a second raster and its metadata against the current raster
        ----------
        self._validate(raster, name)
        Validates an input raster against the current Raster object. Checks that
        the second raster's metadata matches the shape, affine transform, and
        crs of the current object. If the second raster does not have a affine
        transform or CRS, sets these values to match the current raster. Raises
        various RasterErrors if the metadata criteria are not met. Otherwise, returns
        the validated raster dataset as a Raster object.
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

        # Build raster, check shape
        raster = Raster(raster, name)
        if raster.shape != self.shape:
            raise RasterShapeError(
                f"The shape of the {raster.name} {raster.shape}, does not "
                f"match the shape of the {self.name} {self.shape}."
            )

        # Transform
        if raster.transform is None:
            raster._transform = self.transform
        elif raster.transform != self.transform:
            raise RasterTransformError(
                f"The affine transformation of the {raster.name}:\n{raster.transform}\n"
                f"does not match the transform of the {self.name}:\n{self.transform}"
            )

        # CRS
        if raster.crs is None:
            raster._crs = self.crs
        elif raster.crs != self.crs:
            raise RasterCrsError(
                f"The CRS of the {raster.name} ({raster.crs}) does not "
                f"match the CRS of the {self.name} ({self.crs})."
            )
        return raster

    #####
    # IO
    #####

    def save(
        self, path: Pathlike, *, driver: Optional[str] = None, overwrite: bool = False
    ) -> None:
        """
        save  Save a raster dataset to file
        ----------
        self.save(path)
        self.save(path, * overwrite=True)
        Saves the Raster to the indicated path. Boolean rasters will be saved as
        "int8" to accommodate common file format requirements. In the default state,
        the method will raise a FileExistsError if the file already exists. Set
        overwrite=True to enable the replacement of existing files.

        This syntax will attempt to guess the intended file format based on the
        path extension, and raises an Exception if the file format cannot be
        determined. You can use:
            >>> pfdf.utils.driver.extensions('raster')
        to return a summary of the file formats inferred by various extensions.
        We note that pfdf is tested using the "GeoTIFF" file format driver
        (.tif extension), and so saving to this format is likely the most robust.

        self.save(..., *, driver)
        Also specifies the file format driver to use to write the raster file.
        Uses this format regardless of the file extension. You can use:
            >>> pfdf.utils.driver.rasters()
        to return a summary of file-format drivers that are expected to always work.

        More generally, the pfdf package relies on rasterio (which in turn uses
        GDAL) to write raster files, and so additional drivers may work if their
        associated build requirements are satistfied. You can find a complete
        overview of GDAL raster drivers and their requirements here:
        https://gdal.org/drivers/raster/index.html
        ----------
        Inputs:
            path: The path to the saved output file
            overwrite: False (default) to prevent the output from replacing
                existing file. True to allow replacement.
            driver: The name of the file format driver to use to write the file
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
            driver=driver,
            height=self.shape[0],
            width=self.shape[1],
            count=1,
            dtype=dtype,
            nodata=self.nodata,
            transform=self.transform,
            crs=self.crs,
        ) as file:
            file.write(self._values, 1)

    def as_pysheds(self) -> PyshedsRaster:
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

        # Get spatial metadata
        metadata = {"shape": self.shape}
        if self.transform is not None:
            metadata["affine"] = self.transform
        if self.crs is not None:
            metadata["crs"] = self.crs

        # Get nodata or default. Pysheds crashes when using its default NoData 0
        # for boolean rasters, so need to set this explicitly to False
        if self.nodata is None:
            if self.dtype == bool:
                nodata = np.zeros(1, bool)
            else:
                nodata = np.zeros(1, self.dtype)
        else:
            nodata = self.nodata

        # Get viewfinder nodata. Pysheds crashes for certain positive NoData values
        # when using a signed integer raster, so set these initially to -1
        if np.issubdtype(self.dtype, np.signedinteger):
            metadata["nodata"] = -1
        else:
            metadata["nodata"] = nodata

        # Initialize viewfinder and build raster
        view = ViewFinder(**metadata)
        raster = PyshedsRaster(self.values, view)

        # Restore signed integer nodata values
        if np.issubdtype(self.dtype, np.signedinteger):
            raster.nodata = nodata
        return raster


#####
# Type Hints
#####
RasterInput = str | Path | rasterio.DatasetReader | MatrixArray | Raster | PyshedsRaster
