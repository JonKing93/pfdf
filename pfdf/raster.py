"""
raster  A class and type hint for working with raster datasets
----------
This module provides the "Raster" class, which pfdf uses to manage raster datasets.
The class can acquire raster values and metadata from a variety of formats,
and all computed rasters are returned as Raster objects. (And please see the docstring
of the Raster class for additional details). The module also provides the "RasterInput" 
type hint, which denotes all types that pfdf accepts as representing a raster.
----------
Class:
    Raster      - Class that manages raster datasets and metadata

Type Hint:
    RasterInput - Types that are convertible to a Raster object
"""

from math import ceil, floor, inf, sqrt
from pathlib import Path
from typing import Any, Optional, Self

import fiona
import numpy as np
import rasterio
import rasterio.features
import rasterio.transform
from affine import Affine
from pysheds.sview import Raster as PyshedsRaster
from pysheds.sview import ViewFinder
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from rasterio.enums import Resampling

from pfdf._utils import all_nones, no_nones, nodata, real, validate
from pfdf._utils.nodata import NodataMask
from pfdf._utils.transform import Transform
from pfdf.errors import RasterCrsError, RasterShapeError, RasterTransformError
from pfdf.typing import (
    Casting,
    MatrixArray,
    Pathlike,
    RealArray,
    ScalarArray,
    VectorArray,
    scalar,
    shape2d,
)


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
    Alternatively, use the left/right/top/bottom properties to return the spatial
    position of a particular bound. Finally, the dx/dy properties return the change
    in horizontal/vertical coordinates when incrementing one column/row.

    Several other properties describe the pixels in the raster. The "resolution"
    property reports the X-axis and Y-axis spacing between raster pixels. Alternatively,
    use the pixel_height and pixel_width properties to return a single spacing. The
    pixel_area property reports the area of a single pixel, and pixel_diagonal
    reports the length across the diagonal of a single pixel.

    Note that the (affine) transform may only support scaling and translation.
    Shearing is not permitted. Equivalently, the b and d coefficients of the
    transformation matrix must be 0. Also, a number of properties are derived from
    the transform, so will return NaN values if the raster has the transform. As
    follows: dx, dy, bounds, left, right, bottom, top, resolution, pixel_height,
    pixel_width, pixel_area, and pixel_diagonal will return NaN values if there
    is not a transform.

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
        from_array      - Creates a Raster object from a numpy array
        from_file       - Creates a Raster from a file-based dataset
        from_rasterio   - Creates a Raster from a rasterio.DatasetReader object
        from_pysheds    - Creates a Raster from a pysheds.sview.Raster object
        from_polygons   - Creates a raster from (multi)polygon features

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
        dx              - The change in x-axis spatial position when incrementing one column
        dy              - The change in y-axis spatial position when incrementing one row
        bounds          - A BoundingBox with the spatial coordinates of the raster's edges
        left            - The spatial coordinate of the raster's left edge
        right           - The spatial coordinate of the raster's right edge
        top             - The spatial coordinate of the raster's upper edge
        bottom          - The spatial coordinate of the raster's lower edge

    Pixel Properties:
        pixel_width     - The spacing of raster pixels along the X axis in the units of the transform
        pixel_height    - The spacing of raster pixels along the Y axis in the units of the transform
        resolution      - The spacing of raster pixels along the X and Y axes in the units of the transform
        pixel_area      - The area of a raster pixel in the units of the transform squared
        pixel_diagonal  - The length of the diagonal of a raster pixel in the units of the transform

    Comparisons:
        __eq__          - True if the second object is a Raster with the same values, nodata, transform, and crs
        validate        - Checks that a second raster has a compatible shape, transform, and crs

    IO:
        save            - Saves a raster dataset to file
        copy            - Creates a copy of the current Raster
        as_pysheds      - Returns a Raster as a pysheds.sview.Raster object

    Preprocessing:
        fill            - Fills a raster's NoData pixels with the indicated data value
        find            - Returns a boolean raster indicating pixels that match specified values
        set_range       - Forces a raster's data pixels to fall within the indicated range
        buffer          - Buffers the edges of a raster by specified distances
        reproject       - Reprojects a raster to match a specified CRS, resolution, and grid alignment
        clip            - Clips a raster to the specified bounds

    INTERNAL:
    Attributes:
        _name               - Identifying name
        _values             - Saved data values
        _nodata             - NoData value
        _crs                - Coordinate reference system
        _transform          - Affine transformation

    Object creation:
        _match              - Copies the attributes of a template raster to the current raster
        _create             - Creates a new raster from provided values and metadata
        _finalize           - Validate/sets attributes, casts nodata, locks array
        _from_array         - Builds a raster from an array without copying

    From polygons:
        _ring               - Type hint for linear ring coordinate array
        _geometry           - Type hint for a geometry-like dict
        _validate_polygon   - Validates a polygon coordinate array
        _update_bounds      - Updates bounds to contain a polygon
        _validate_feature   - Validates a polygon feature and extracts geometry
        _validate_field     - Checks that a data field exists and has an int or float type

    Generic Metadata:
        _validate_shape     - Validates a raster shape
        _validate_spatial   - Validates CRS and transform
        _validate_nodata    - Validates NoData and casting
        _validate_metadata  - Validates CRS, transform, NoData, and casting
        _parse_template     - Parses values from a template and keyword options
        _set_metadata       - Sets the CRS, transform, and NoData attributes

    Preprocessing Metadata:
        _EdgeDict           - Type hint for an edge: value, resolution dict
        _edge_dict          - Builds a dict with a value and resolution for each edge
        _parse_metadatas    - Determines source and template metadata values
        _parse_nodata       - Parses nodata from the current raster and keyword input

    Numeric Preprocessing:
        _validate_bound     - Checks a bound is castable or returns a default if not provided

    Buffering:
        _validate_distance  - Checks a buffering distance is a positive scalar
        _validate_buffer    - Gets the buffer for a direction, using a default if needed
        _compute_buffers    - Validates buffers and computes pixels in each direction
        _buffer             - Buffers the raster by the specified number of pixels in each direction

    Reprojection:
        _validate_resampling    - Validates a resampling option
        _alignment          - Computes shape and transform of an aligned reprojection
        _align_edge         - Locates an aligned left or top edge
        _axis_length        - Determines the length of reprojected axis

    Clipping:
        _parse_bounds       - Parses bounds from keywords, template, and current bounds
        _validate_orientation   - Checks that clipping bounds match the current orientation
        _clipped_values     - Returns that data array and NoData for a clipped raster
        _clip_interior      - Clips a raster to a subset of its current bounds
        _clip_exterior      - Clips a raster to include areas outside the current bounds
        _clip_indices       - Returns the indices of pixels in the current and clipped raster
    """

    #####
    # Properties
    #####

    ##### Data

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        validate.type(name, "raster name", str, "string")
        self._name = name

    @property
    def values(self) -> np.ndarray:
        if self._values is None:
            return None
        else:
            return self._values.view()

    @property
    def dtype(self) -> np.dtype:
        if self._values is None:
            return None
        else:
            return self._values.dtype

    @property
    def nodata(self) -> scalar:
        return self._nodata

    ##### Shape

    @property
    def shape(self) -> shape2d:
        if self._values is None:
            return (0, 0)
        else:
            return self._values.shape

    @property
    def height(self) -> int:
        return self.shape[0]

    @property
    def width(self) -> int:
        return self.shape[1]

    @property
    def size(self) -> int:
        nrows, ncols = self.shape
        return nrows * ncols

    ##### Spatial

    @property
    def crs(self) -> CRS:
        return self._crs

    @crs.setter
    def crs(self, crs: CRS) -> None:
        if self._crs is not None:
            raise ValueError(
                "Cannot set the CRS because the raster already has a CRS. "
                "See the 'reproject' method to change a raster's CRS."
            )
        self._crs = validate.crs(crs)

    @property
    def transform(self) -> Affine:
        return self._transform.affine

    @transform.setter
    def transform(self, transform: Affine) -> None:
        if self.transform is not None:
            raise ValueError(
                "Cannot set the transform because the raster already has a transform. "
                "See the 'reproject' method to change a raster's transform."
            )
        self._transform = Transform(transform)

    @property
    def dx(self) -> float:
        return self._transform.dx

    @property
    def dy(self) -> float:
        return self._transform.dy

    @property
    def left(self) -> float:
        return self._transform.left

    @property
    def top(self) -> float:
        return self._transform.top

    @property
    def right(self) -> float:
        return self._transform.right(self.width)

    @property
    def bottom(self) -> float:
        return self._transform.bottom(self.height)

    @property
    def bounds(self) -> BoundingBox:
        return self._transform.bounds(self.shape)

    ##### Pixels

    @property
    def pixel_width(self) -> float:
        return self._transform.xres

    @property
    def pixel_height(self) -> float:
        return self._transform.yres

    @property
    def resolution(self) -> tuple[float, float]:
        return self._transform.resolution

    @property
    def pixel_area(self) -> float:
        width, height = self.resolution
        return width * height

    @property
    def pixel_diagonal(self) -> float:
        width, height = self.resolution
        return sqrt(width**2 + height**2)

    # Type hint equivalent to RasterInput, but using "Self" instead of "Raster"
    _RasterInput = (
        Self | str | Path | rasterio.DatasetReader | MatrixArray | PyshedsRaster
    )

    #####
    # Init
    #####

    def __init__(
        self,
        raster: Optional[_RasterInput] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        __init__  Creates a new Raster object
        ----------
        Raster(raster)
        Returns the input raster as a Raster object. Supports a variety of raster
        datasets including: the path to a file-based raster, numpy arrays, other
        pfdf.raster.Raster objects, and pysheds.sview.Raster objects. The input
        raster should refer to a 2D array with a boolean, integer, or floating
        dtype - raises Exceptions when this is not the case.

        Note that this constructor will attempt to determine the type of input,
        and initialize a raster using default option for that input type.
        Alternatively, you can use the various factory methods to create various
        types of rasters with additional options. For example, the "from_array"
        method allows you to create a raster from a numpy array while also including
        spatial metadata and NoData values. Separately, the "from_file" method
        allows you to specify the band and file-format driver to use when reading
        a raster from file.

        Raster(raster, name)
        Optionally specifies a name for the raster. This can be returned using
        the ".name" property, and is used to identify the raster in error messages.
        Defaults to "raster" if unspecified.

        Raster()
        Returns an empty raster object. The attributes of the raster are all set
        to None. This syntax is typically not useful for users, and is instead
        intended for developers.
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
        self._values: Optional[MatrixArray] = None
        self._nodata: Optional[ScalarArray] = None
        self._crs: Optional[CRS] = None
        self._transform: Transform = Transform(None)

        # Set name
        if name is None:
            name = "raster"
        self.name = name

        # If no inputs were provided, just return the empty object
        if raster is None:
            return

        # Otherwise, build an object using a factory
        elif isinstance(raster, (str, Path)):
            raster = Raster.from_file(raster, name)
        elif isinstance(raster, rasterio.DatasetReader):
            raster = Raster.from_rasterio(raster, name)
        elif isinstance(raster, PyshedsRaster):
            raster = Raster.from_pysheds(raster, name)
        elif isinstance(raster, np.ndarray):
            raster = Raster.from_array(raster, name)

        # Error if the input is not recognized
        elif not isinstance(raster, Raster):
            raise TypeError(
                f"{self.name} is not a recognized type. Allowed types are: "
                "str, pathlib.Path, rasterio.DatasetReader, 2d numpy.ndarray, "
                "pfdf.raster.Raster, and pysheds.sview.Raster objects."
            )

        # Set attributes to the values from the factory object
        self._match(raster)

    def _match(self, template: Self) -> None:
        "Copies the attributes from a template raster to the current raster"
        self._values = template._values
        self._set_metadata(template._crs, template._transform, template._nodata)

    #####
    # Factories
    #####

    @staticmethod
    def _create(
        name: Any, values: Any, crs: Any, transform: Any, nodata: Any, casting: Any
    ) -> Self:
        "Creates a new raster from the provided values and metadata"
        raster = Raster(None, name)
        raster._finalize(values, crs, transform, nodata, casting)
        return raster

    def _finalize(
        self, values: Any, crs: Any, transform: Any, nodata: Any, casting: Any
    ) -> None:
        """Validates and sets array values and metadata. Casts NoData to the dtype
        of the raster. Converts affine to Transform object. Locks array values as read-only
        """

        # Validate array values, metadata, and NoData casting
        self._values = validate.matrix(values, self.name, dtype=real)
        crs, transform, nodata = self._validate_metadata(
            crs, transform, nodata, casting, self.dtype
        )
        transform = Transform(transform)

        # Set metadata and lock the array values. This prevents users from altering
        # the base array when using views of the data values
        self._set_metadata(crs, transform, nodata)
        self._values.setflags(write=False)

    @staticmethod
    def from_file(
        path: Pathlike,
        name: Optional[str] = None,
        *,
        driver: Optional[str] = None,
        band: int = 1,
        isbool: bool = False,
    ) -> Self:
        """
        Builds a Raster object from a file-based dataset
        ----------
        Raster.from_file(path)
        Raster.from_file(path, name)
        Builds a Raster from the indicated file. Raises a FileNotFoundError if
        the file cannot be located. Loads file data when building the object
        By default, loads all data from band 1, but see below for additional options.
        The name input can be used to provide an optional name for the raster,
        defaults to "raster" if unset.

        Also, by default the method will attempt to use the file extension to
        detect the file format driver used to read data from the file. Raises an
        Exception if the driver cannot be determined, but see below for options
        to explicitly set the driver. You can also use:
            >>> pfdf.utils.driver.extensions('raster')
        to return a summary of supported file format drivers, and their associated
        extensions.

        Raster.from_file(..., *, band)
        Specify the raster band to read. Raster bands use 1-indexing (and not the
        0-indexing common to Python). Raises an error if the band does not exist.

        Raster.from_file(..., *, driver)
        Specify the file format driver to use for reading the file. Uses this
        driver regardless of the file extension. You can also call:
            >>> pfdf.utils.driver.rasters()
        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on rasterio (which in turn uses GDAL/OGR)
        to read raster files, and so additional drivers may work if their
        associated build requirements are met. A complete list of driver build
        requirements is available here: https://gdal.org/drivers/raster/index.html

        Raster.from_file(..., *, isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the file data values. The newly created raster will have a bool
        dtype and values, and its NoData value will be set to False. When using
        this option, all data pixels in the original file must be equal to 0 or
        1. NoData pixels in the file will be converted to False, regardless of
        their value.
        ----------
        Inputs:
            path: A path to a file-based raster dataset
            name: An optional name for the raster
            band: The raster band to read. Uses 1-indexing and defaults to 1
            driver: A file format to use to read the raster, regardless of extension
            isbool: True to convert the raster to a boolean array, with nodata=False.
                False (default) to leave the raster as the original dtype.

        Outputs:
            Raster: A Raster object for the file-based dataset
        """

        # Validate inputs and initialize Raster
        path = validate.input_path(path, "path")
        if driver is not None:
            validate.type(driver, "driver", str, "string")
        validate.type(band, "band", int, "int")

        # Open file. Get data values and metadata
        with rasterio.open(path) as file:
            values = file.read(band)
            crs = file.crs
            transform = file.transform
            nodata = file.nodata

        # Optionally convert to boolean array and return the Raster
        if isbool:
            values = validate.boolean(values, "the saved raster", ignore=nodata)
            nodata = False
        return Raster._create(name, values, crs, transform, nodata, "unsafe")

    @staticmethod
    def from_rasterio(
        reader: rasterio.DatasetReader, name: Optional[str] = None, band: int = 1
    ) -> Self:
        """
        from_rasterio  Builds a raster from a rasterio.DatasetReader
        ----------
        Raster.from_rasterio(reader)
        Raster.from_rasterio(reader, name)
        Creates a new Raster object from a rasterio.DatasetReader object. Raises a
        FileNotFoundError if the associated file no longer exists. Uses the file
        format driver associated with the object to read the raster from file.
        By default, loads the data from band 1. The name input specifies an optional
        name for the new Raster object. Defaults to "raster" if unset.

        Raster.from_rasterio(..., band)
        Specifies the file band to read when loading the raster from file. Raster
        bands use 1-indexing (and not the 0-indexing common to Python). Raises an
        error if the band does not exist.
        ----------
        Inputs:
            reader: A rasterio.DatasetReader associated with a raster dataset
            name: An optional name for the raster. Defaults to "raster"
            band: The raster band to read. Uses 1-indexing and defaults to 1

        Outputs:
            Raster: The new Raster object
        """

        # Validate and get linked path. Informative error if file is missing
        validate.type(
            reader,
            "input raster",
            rasterio.DatasetReader,
            "rasterio.DatasetReader object",
        )
        path = Path(reader.name)
        if not path.exists():
            raise FileNotFoundError(
                f"The file associated with the input rasterio.DatasetReader "
                f"object no longer exists.\nFile: {path}"
            )

        # Use the file factory with the recorded driver
        return Raster.from_file(path, name, driver=reader.driver, band=band)

    @staticmethod
    def from_pysheds(sraster: PyshedsRaster, name: Optional[str] = None) -> Self:
        """
        from_pysheds  Creates a Raster from a pysheds.sview.Raster object
        ----------
        Raster.from_pysheds(sraster)
        Raster.from_pysheds(sraster, name)
        Creates a new Raster object from a pysheds.sview.Raster object. Inherits
        the nodata values, CRS, and transform of the pysheds Raster. Creates a
        copy of the input raster's data array, so changes to the pysheds raster
        will not affect the new Raster object, and vice versa. The name input
        specifies an optional name for the new Raster. Defaults to "raster" if
        unset.
        ----------
        Inputs:
            sraster: The pysheds.sview.Raster object used to create the new Raster
            name: An optional name for the raster. Defaults to "raster"

        Outputs:
            Raster: The new Raster object
        """

        validate.type(
            sraster, "input raster", PyshedsRaster, "pysheds.sview.Raster object"
        )
        crs = CRS.from_wkt(sraster.crs.to_wkt())
        values = np.array(sraster, copy=True)
        return Raster._create(
            name, values, crs, sraster.affine, sraster.nodata, casting="unsafe"
        )

    @staticmethod
    def _from_array(
        array: MatrixArray, *, crs: Any, transform: Any, nodata: Any
    ) -> Self:
        "Builds a Raster from optional metadata and a validated array without copying"
        return Raster._create(None, array, crs, transform, nodata, casting="safe")

    @staticmethod
    def from_array(
        array: MatrixArray,
        name: Optional[str] = None,
        *,
        nodata: Optional[scalar] = None,
        transform: Optional[Affine] = None,
        crs: Optional[CRS | Any] = None,
        spatial: Optional[Self] = None,
        casting: Casting = "safe",
    ) -> Self:
        """
        from_array  Add raster metadata to a raw numpy array
        ----------
        Raster.from_array(array, name)
        Initializes a Raster object from a raw numpy array. The NoData value,
        transform, and crs for the returned object will all be None. The raster
        name can be returned using the ".name" property and is used to identify
        the raster in error messages. Defaults to 'raster' if unset. Note that
        the new Raster object holds a copy of the input array, so changes to the
        input array will not affect the Raster, and vice-versa.

        Raster.from_array(..., *, nodata)
        Raster.from_array(..., *, nodata, casting)
        Specifies a NoData value for the raster. The NoData value will be set to
        the same dtype as the array. Raises a TypeError if the NoData value cannot
        be safely casted to this dtype. Use the casting option to change this
        behavior. Casting options are as follows:
        'no': The data type should not be cast at all
        'equiv': Only byte-order changes are allowed
        'safe': Only casts which can preserve values are allowed
        'same_kind': Only safe casts or casts within a kind (like float64 to float32)
        'unsafe': Any data conversions may be done

        Raster.from_array(..., *, spatial)
        Specifies a Raster object to use as a default spatial metadata template.
        By default, transform and crs properties from the template will be copied
        to the new raster. However, see below for a syntax to override this behavior.

        Raster.from_array(..., *, transform)
        Raster.from_array(..., *, crs)
        Specifies the crs and/or transform that should be associated with the
        raster. If used in conjunction with the "spatial" option, then any keyword
        options will take precedence over the metadata in the spatial template.

        The transform specifies the affine transformation used to map pixel indices
        to spatial points, and should be an affine.Affine object. Common ways
        to obtain such an object are using the ".transform" property from rasterio
        and Raster objects, via the ".affine" property of pysheds rasters, or via
        the Affine class itself.

        The crs is the coordinate reference system used to locate spatial points.
        This input should a rasterio.crs.CRS object, or convertible to such an
        object. CRS objects can be obtained using the ".crs" property from rasterio
        or Raster objects, and see also the rasterio documentation for building
        these objects from formats such as well-known text (WKT) and PROJ4 strings.
        ----------
        Inputs:
            array: A 2D numpy array whose data values represent a raster
            name: A name for the raster. Defaults to 'raster'
            nodata: A NoData value for the raster
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
            spatial: A Raster object to use as a default spatial metadata template
                for the new Raster.
            transform: An affine transformation for the raster (affine.Affine)
            crs: A coordinate reference system for the raster (rasterio.crs.CRS)

        Outputs:
            Raster: A raster object for the array-based raster dataset
        """

        # Validate metadata. Parse from template and keyword options
        crs, transform, nodata = Raster._validate_metadata(
            crs, transform, nodata, casting
        )
        metadata = Raster._parse_template(
            spatial, "spatial template", {"crs": crs, "transform": transform}
        )

        # Copy array and build the object
        values = np.array(array, copy=True)
        return Raster._create(
            name, values, metadata["crs"], metadata["transform"], nodata, casting
        )

    #####
    # From Polygon
    #####

    _ring = list[tuple[float, float]]
    _geometry = dict[str, Any]

    @staticmethod
    def _validate_field(field: Any, schema: dict[str, str]) -> None:
        "Checks that a data property field can be used to build a raster"

        # Just exit if there isn't a field
        if field is None:
            return

        # Must be one of the property keys
        validate.type(field, "field", str, "str")
        fields = schema.keys()
        if field not in fields:
            allowed = ", ".join(fields)
            raise KeyError(
                f"'{field}' is not the name of a polygon data field. "
                f"Allowed field names are: {allowed}"
            )

        # Must be an int or float type
        typestr = schema[field]
        if not typestr.startswith(("int", "float")):
            typestr = typestr.split(":")[0]
            raise TypeError(
                f"The '{field}' field is not an int or float. Instead, it has a '{typestr}' type."
            )

    @staticmethod
    def _validate_polygon(f: int, p: int, rings: Any) -> None:
        """Validates a polygon coordinate array
        f: Index of the feature, p: index of the polygon in the feature"""

        # Must be a list of linear rings
        if not isinstance(rings, list):
            raise ValueError(
                "The coordinates array for each polygon must be a list of linear "
                f"ring coordinates. However in feature[{f}], the coordinates array "
                f"for polygon[{p}] is not a list."
            )

        # Validate each ring. Check each is a list of coordinates...
        for r, ring in enumerate(rings):
            if not isinstance(ring, list):
                raise ValueError(
                    f"Each element of a polygon's coordinates array must be a list "
                    f"of linear ring coordinates. However in feature[{f}], "
                    f"polygon[{p}].coordinates[{r}] is not a list."
                )

            # ... with at least 4 coordinates...
            elif len(ring) < 4:
                raise ValueError(
                    f"Each linear ring must have at least 4 positions. However "
                    f"ring[{r}] in polygon[{p}] of feature[{f}] does not have "
                    f"4 positions."
                )

            # ... and matching start/end positions
            elif ring[0] != ring[-1]:
                raise ValueError(
                    f"The final position in each linear ring must match the first "
                    f"position. However, this is not the case for ring[{r}] in "
                    f"polygon[{p}] of feature[{f}]."
                )

    @staticmethod
    def _update_bounds(coords: list[_ring], bounds: bounds) -> None:
        "Updates bounds to contain a polygon"

        # Get the bounds of the shell
        shell = np.array(coords[0])
        left = np.min(shell[:, 0])
        right = np.max(shell[:, 0])
        bottom = np.min(shell[:, 1])
        top = np.max(shell[:, 1])

        # Ensure the bounds contain the shell
        bounds["left"] = min(bounds["left"], left)
        bounds["right"] = max(bounds["right"], right)
        bounds["bottom"] = min(bounds["bottom"], bottom)
        bounds["top"] = max(bounds["top"], top)

    @staticmethod
    def _validate_feature(
        f: int, feature: dict[str, Any], bounds: dict[str, float], field: str | None
    ) -> tuple[_geometry, int | float | bool]:
        "Validates a polygon feature, extracts geometry, and updates bounds"

        # Require a geometry
        geometry = feature["geometry"]
        if geometry is None:
            raise ValueError(
                f"Feature[{f}] does not have a geometry, or its geometry is not valid."
            )

        # Only allow Polygon and MultiPolygon geometries
        type = geometry["type"]
        if type not in ["Polygon", "MultiPolygon"]:
            raise ValueError(
                "Each feature in the input file must have a Polygon or MultiPolygon "
                f"geometry. However, feature[{f}] has a {type} geometry instead."
            )

        # Get a list of polygon coordinate arrays in the feature
        polygons = geometry["coordinates"]
        if type == "Polygon":
            polygons = [polygons]

        # Validate coordinates and update bounds
        for p, polygon in enumerate(polygons):
            Raster._validate_polygon(f, p, polygon)
            Raster._update_bounds(polygon, bounds)

        # Get the pixel values for the polygon
        if field is None:
            value = True
        else:
            value = feature["properties"][field]

        # Return geometry and data field if relevant
        return geometry, value

    @staticmethod
    def from_polygons(
        path: Pathlike,
        *,
        field: Optional[str] = None,
        fill: Optional[scalar] = None,
        resolution: Optional[scalar | tuple[scalar, scalar] | Self] = 1,
        layer: Optional[int | str] = None,
        driver: Optional[str] = None,
        encoding: Optional[str] = None,
    ) -> Self:
        """
        Raster.from_polygons(path)
        Raster.from_polygons(path, *, layer)
        Returns a boolean raster derived from the input polygon features. Pixels
        whose centers are in any of the polygons are set to True. All other pixels
        are set to False. The CRS of the output raster is inherited from the input
        feature file. The default resolution of the output raster is 1 (in the
        units of the polygon's CRS), although see below for options for other
        resolutions. The bounds of the raster will be the minimal bounds required
        to contain all input polygons at the indicated resolution.

        The contents of the input file should resolve to a FeatureCollection of
        Polygon and/or MultiPolygon geometries. If the file contains multiple
        layers, you can use the "layer" option to indicate the layer that holds
        the polygon geometries. This may either be an integer index, or the name
        of the layer in the input file.

        By default, this method will attempt to guess the intended file format and
        encoding based on the path extension. Raises an error if the format or
        encoding cannot be determined. However, see below for syntax to specify
        the driver and encoding, regardless of extension. You can also use:
            >>> pfdf.utils.driver.extensions('vector')
        to return a summary of supported file format drivers, and their associated
        extensions.

        Raster.from_polygons(..., *, field)
        Raster.from_polygons(..., *, field, fill)
        Builds the raster using the indicated field of the polygon data properties.
        The specified field must exist in the data properties, and must be an int
        or float type. The output raster will have a float dtype, regardless of
        the type of the data field, and the NoData value will be NaN. Pixels whose
        centers are in a polygon are set to the value of the data field for that
        polygon. If a pixel is in multiple  overlapping polygons, then the pixel's
        value will match the data field of the final polygon in the set. By
        default, all pixels not in a polygon are set as Nodata (NaN). Use the
        "fill" option to specify a default data value for these pixels instead.

        Raster.from_polygons(path, *, resolution)
        Specifies the resolution of the output raster. The resolution may be a
        scalar positive number, a 2-tuple of such numbers, or a pfdf.raster.Raster
        object. If a scalar, indicates the resolution of the output raster (in the
        units of the CRS) for both the X and Y axes. If a 2-tuple, the first element
        is the X-axis resolution and the second element is the Y-axis. If a Raster,
        uses the resolution of the raster, or raises an error if the raster does
        not have a transform.

        Raster.from_polygons(..., *, driver)
        Raster.from_polygons(..., *, encoding)
        Specifies the file format driver and encoding used to read the polygon
        feature file. Uses this format regardless of the file extension. You can call:
            >>> pfdf.utils.driver.vectors()
        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR)
        to read vector files, and so additional drivers may work if their
        associated build requirements are met. You can call:
            >>> fiona.drvsupport.vector_driver_extensions()
        to summarize the drivers currently supported by fiona, and a complete
        list of driver build requirements is available here:
        https://gdal.org/drivers/vector/index.html
        ----------
        Inputs:
            path: The path to a Polygon or MultiPolygon feature file
            field: The name of a data property field used to set pixel values.
                The data field must have an int or float type.
            fill: A default fill value for rasters built using a data field.
                Ignored if field is None.
            resolution: The desired resolution of the output raster
            layer: The layer of the input file from which to load the polygon geometries
            driver: The file-format driver to use to read the polygon feature file
            encoding: The encoding of the polygon feature file

        Outputs:
            Raster: The polygon-derived raster. Pixels whose centers are in a
                polygon are set either to True, or to the value of a data field.
                All other pixels are NoData (False or NaN, as appropriate).
        """

        # Validate path and resolution
        path = validate.input_path(path, "path")
        if isinstance(resolution, Raster):
            if resolution.transform is None:
                raise ValueError(
                    f"Cannot use the input raster to specify resolution because the "
                    f"raster does not have an affine transform."
                )
            resolution = resolution.resolution
        else:
            resolution = validate.resolution(resolution)

        # Settings for boolean rasters
        if field is None:
            dtype = "uint8"
            nodata = False
            fill = False

        # Settings for data field rasters
        else:
            dtype = float
            nodata = np.nan
            if fill is None:
                fill = nodata
            else:
                fill = float(validate.scalar(fill, "fill", dtype=real))

        # Open file. Validate field. Load CRS and features
        with fiona.open(path, layer=layer, driver=driver, encoding=encoding) as file:
            Raster._validate_field(field, file.schema["properties"])
            crs = file.crs
            features = list(file)

        # Initialize spatial bounds
        bounds = {
            "left": inf,
            "right": -inf,
            "bottom": inf,
            "top": -inf,
        }

        # Validate features and extract geometries. Also update spatial bounds
        # to contain all validated features
        for f, feature in enumerate(features):
            features[f] = Raster._validate_feature(f, feature, bounds, field)

        # Compute the shape and transform of the output raster
        dx, dy = resolution
        height = bounds["top"] - bounds["bottom"]
        width = bounds["right"] - bounds["left"]
        nrows = ceil(height / dy)
        ncols = ceil(width / dx)
        transform = Transform.build(dx, -dy, bounds["left"], bounds["top"])

        # Rasterize the polygon features
        raster = rasterio.features.rasterize(
            features,
            out_shape=[nrows, ncols],
            transform=transform,
            fill=fill,
            dtype=dtype,
        )

        # Build final Raster object. Convert to boolean as appropriate
        if field is None:
            raster = raster.astype(bool)
        return Raster._from_array(raster, crs=crs, transform=transform, nodata=nodata)

    #####
    # Generic Metadata Utilities
    #####

    @staticmethod
    def _validate_shape(shape: Any) -> shape2d | None:
        "Validates optional raster shape metadata"

        if shape is not None:
            shape = validate.vector(shape, "shape", dtype=real, length=2)
            validate.positive(shape, "shape")
            validate.integers(shape, "shape")
            shape = (int(shape[0]), int(shape[1]))
        return shape

    @staticmethod
    def _validate_spatial(crs: Any, transform: Any) -> tuple[CRS | None, Affine | None]:
        "Validates optional CRS and transform metadata"

        if crs is not None:
            crs = validate.crs(crs)
        if transform is not None:
            transform = validate.transform(transform)
        return crs, transform

    @staticmethod
    def _validate_nodata(nodata: Any, casting, dtype: Optional[Any] = None):
        """Validates Nodata casting option and optional NoData metadata. If a dtype
        is provided, also validates casting and returns the casted NoData value"""

        # Validate casting option and optional NoData value
        casting = validate.option(
            casting, "casting", allowed=["no", "equiv", "safe", "same_kind", "unsafe"]
        )
        if nodata is not None:
            nodata = validate.scalar(nodata, "nodata", dtype=real)
            nodata = nodata[0]

            # Optionally validate casting and cast the NoData value
            if dtype is not None:
                nodata = validate.casting(nodata, "the NoData value", dtype, casting)
        return nodata

    @staticmethod
    def _validate_metadata(
        crs: Any, transform: Any, nodata: Any, casting: Any, dtype=None
    ) -> tuple[CRS | None, Transform, ScalarArray | None]:
        "Validates optional CRS, transform, nodata, and casting"

        crs, transform = Raster._validate_spatial(crs, transform)
        nodata = Raster._validate_nodata(nodata, casting, dtype)
        return crs, transform, nodata

    @staticmethod
    def _parse_template(
        template: Self | None, name: str, fields: dict[str, Any | None]
    ) -> dict[str, Any]:
        "Parses metadata values from a template Raster and keyword options"

        # Require template to be a Raster
        if template is not None:
            validate.type(template, name, Raster, "pfdf.raster.Raster object")

        # Prioritize keywords options, but use template metadata as backup
        if template is not None:
            for field, value in fields.items():
                if value is None:
                    fields[field] = getattr(template, field)
        return fields

    def _set_metadata(self, crs: Any, transform: Any, nodata: Any) -> None:
        "Sets the CRS, transform, and NoData attributes"
        self._crs = crs
        self._transform = transform
        self._nodata = nodata

    #####
    # Comparisons
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

        return (
            isinstance(other, Raster)
            and nodata.equal(self.nodata, other.nodata)
            and self.transform == other.transform
            and self.crs == other.crs
            and np.array_equal(self.values, other.values, equal_nan=True)
        )

    def validate(self, raster: _RasterInput, name: str) -> Self:
        """
        validate  Validates a second raster and its metadata against the current raster
        ----------
        self.validate(raster, name)
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
            raster._transform = self._transform
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
        self,
        path: Pathlike,
        *,
        driver: Optional[str] = None,
        overwrite: bool = False,
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

        copy = Raster(None, self.name)
        copy._match(self)
        return copy

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
    # Preprocessing Metadata Utilities
    #####

    _EdgeDict = dict[str, tuple[float, float]]

    @staticmethod
    def _edge_dict(
        left: float,
        right: float,
        top: float,
        bottom: float,
        width: float,
        height: float,
    ) -> _EdgeDict:
        "Builds a dict with a value and resolution for each edge"

        return {
            "left": (left, width),
            "right": (right, width),
            "top": (top, height),
            "bottom": (bottom, height),
        }

    @staticmethod
    def _parse_metadatas(
        source: Any, template: Any, default: Any = None
    ) -> dict[str, Any]:
        "Determines source and template metadata values"

        if no_nones(source, template):
            metadata = source, template
        elif all_nones(source, template):
            metadata = default, default
        elif source is None and template is not None:
            metadata = template, template
        else:
            metadata = source, source
        return {"source": metadata[0], "template": metadata[1]}

    def _parse_nodata(self, nodata: Any, casting: Any) -> ScalarArray:
        "Parses a Nodata value from the current raster and a keyword input"

        # Require exactly 1 NoData value
        if all_nones(self.nodata, nodata):
            raise ValueError(
                "Cannot continue because the raster does not have a NoData value. "
                "Use the 'nodata' input to provide a NoData value for the raster."
            )
        elif no_nones(self.nodata, nodata):
            raise ValueError(
                "You cannot provide a NoData value because the raster already has "
                "a NoData value."
            )

        # Use current value or validate user input
        elif nodata is None:
            return self.nodata
        else:
            return self._validate_nodata(nodata, casting, self.dtype)

    #####
    # Numeric Preprocessing
    #####

    def fill(self, value: ScalarArray) -> None:
        """
        fill  Replaces NoData pixels with the indicated value
        ----------
        self.fill(value)
        Locates NoData pixels in the raster and replaces them with the indicated
        value. The fill value must be safely castable to the dtype of the raster.
        Note that this method creates a copy of the raster's data array before
        replacing NoData values. As such, other copies of the raster will not be
        affected. Also note that the updated raster will no longer have a NoData
        value, as all NoData pixels will have been replaced.
        ----------
        Inputs:
            value: The fill value that NoData pixels will be replaced with
        """

        # Validate the fill value
        value = validate.scalar(value, "fill value", dtype=real)
        value = validate.casting(value, "fill value", self.dtype, casting="safe")

        # Just exit if there's not a NoData Value
        if self.nodata is None:
            return

        # Locate NoData values, copy the array, then fill the copy
        nodatas = NodataMask(self.values, self.nodata)
        data = self.values.copy()
        nodatas.fill(data, value)

        # Update the raster object
        self._finalize(data, self.crs, self.transform, nodata=None, casting="unsafe")

    def find(self, values: RealArray) -> Self:
        """
        Returns a boolean raster indicating pixels that match specified values
        ----------
        self.find(values)
        Searches for the input values within the current raster. Returns a boolean
        raster the same size as the current raster. True pixels indicate pixels
        that matched one of the input values. All other pixels are False.
        ----------
        Inputs:
            values: An array of values that the raster values should be compared against.

        Outputs:
            Raster: A boolean raster. True elements indicate pixels that matched
                one of the input values. All other pixels are False
        """

        # Validate, then locate values in the raster
        values = validate.array(values, "values", dtype=real)
        isin = np.isin(self.values, values)

        # Also support NaN searches
        if np.any(np.isnan(values)):
            nans = np.isnan(self.values)
            isin = isin | nans
        return Raster._from_array(
            isin, crs=self.crs, transform=self.transform, nodata=False
        )

    def set_range(
        self,
        min: Optional[scalar] = None,
        max: Optional[scalar] = None,
        fill: bool = False,
        nodata: Optional[scalar] = None,
        casting: str = "safe",
    ) -> None:
        """
        set_range  Forces a raster's data values to fall within specified bounds
        ----------
        self.set_range(min, max)
        Forces the raster's data values to fall within a specified range. The min
        and max inputs specify inclusive lower and upper bounds for the range, and
        must be safely castable to the dtype of the raster. Data values that fall
        outside these bounds are clipped - pixels less than the lower bound are
        set to equal the bound, and pixels greater than the upper bound are set
        to equal that bound. If a bound is None, does not enforce that bound.
        Raises an error if both bounds are None. Note that the min and max inputs
        must be safely castable to the dtype of the raster.

        This method creates a copy of the raster's data values before replacing
        out-of-bounds pixels, so copies of the raster are not affected. Also, the
        method does not alter NoData pixels, even if the NoData value is outside
        of the indicated bounds.

        self.set_range(..., fill=True)
        Indicates that pixels outside the bounds should be replaced with the
        raster's NoData value, instead of being clipped to the appropriate bound.
        Raises a ValueError if the raster does not have a NoData value, although
        see the next syntax for options to resolve this.

        self.set_range(..., fill=True, nodata)
        self.set_range(..., fill=True, nodata, casting)
        Specifies a NoData value when using the "fill" option for a raster that
        does not have a NoData value. These inputs are ignored when fill=False.
        If fill=True, then they are only available if the raster does not have a
        NoData value - otherwise, raises an error. By default, the nodata value
        must be safely castable to the raster dtype. Use the "casting" input to
        allow other casting options.
        ----------
        Inputs:
            min: A lower bound for the raster
            max: An upper bound for the raster
            fill: If False (default), clips pixels outside the bounds to bounds.
                If True, replaces pixels outside the bounds with the NoData value
            nodata: A NoData value for when fill=True and the raster does not have
                a NoData value. Ignored if fill=False
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
        """

        # Validate bounds and NoData
        min = self._validate_bound(min, "min")
        max = self._validate_bound(max, "max")
        if fill:
            nodata = self._parse_nodata(nodata, casting)

        # Locate out-of-bounds data pixels
        values = self.values
        data = NodataMask(values, self.nodata, invert=True)
        high = data & (values > max)
        low = data & (values < min)

        # If filling, set fill values to NoData
        if fill:
            min = nodata
            max = nodata

        # If not filling, ignore nodata inputs and retain current value
        else:
            nodata = self.nodata

        # Replace out-of-bounds values
        values = values.copy()
        high.fill(values, max)
        low.fill(values, min)
        self._finalize(values, self.crs, self.transform, nodata, casting="safe")

    def _validate_bound(self, value: Any, bound: str) -> ScalarArray:
        """Checks that a user provided bound is castable or provides a default
        bound if no value was provided"""

        # Get default bounds. Bool default is True or False
        if value is None:
            if self.dtype == bool:
                return bound == "max"

            # Integer default is the min/max value representable in the dtype
            elif np.issubdtype(self.dtype, np.integer):
                info = np.iinfo(self.dtype)
                return getattr(info, bound)

            # Floating default is -inf/inf
            elif bound == "min":
                return -inf
            else:
                return inf

        # Otherwise, validate user values
        else:
            value = validate.scalar(value, bound, dtype=real)
            value = validate.casting(value, bound, self.dtype, "safe")
            return value

    #####
    # Buffering
    #####

    @staticmethod
    def _validate_distance(distance: Any, name: str) -> ScalarArray:
        "Checks that a buffering distance is valid"
        distance = validate.scalar(distance, name)
        validate.positive(distance, name, allow_zero=True)
        return distance

    @staticmethod
    def _validate_buffer(buffer: Any, name: str, default: ScalarArray) -> ScalarArray:
        "Validates and returns the buffer for a direction"
        if buffer is None:
            return default
        else:
            return Raster._validate_distance(buffer, name)

    def buffer(
        self,
        distance: Optional[scalar] = None,
        *,
        left: Optional[scalar] = None,
        bottom: Optional[scalar] = None,
        right: Optional[scalar] = None,
        top: Optional[scalar] = None,
        pixels: bool = False,
        nodata: Optional[scalar] = None,
        casting: Casting = "safe",
    ) -> None:
        """
        Buffers the current raster by a specified minimum distance
        ----------
        self.buffer(distance)
        Buffers the current raster by the specified minimum distance and returns the
        buffered raster. Buffering adds a number of NoData pixels to each edge of the
        raster's data value matrix, such that the number of pixels is as least as long
        as the specified distance. If the specified distance is not a multiple of an
        axis's resolution, then the buffering distance along that axis will be longer
        than the input distance. Also note that the number of pixels added to the x
        and y axes can differ if these axes have different resolutions.

        The input distance cannot be negative, and should be in the same units as
        the raster's affine transformation. In practice, this is often units of
        meters. Raises an error if the raster does not have an affine transformation,
        but see below for an option that does not require a transform. Similarly,
        the default syntax requires the raster to have a NoData value, but see below
        for a syntax that relaxes this requirement.

        self.buffer(*, left)
        self.buffer(*, right)
        self.buffer(*, bottom)
        self.buffer(*, top)
        Specify the distance for a particular direction. The "distance" input is
        optional (but still permitted) if any of these options are specified. If
        both the "distance" input and one of these options are specified, then
        the direction-specific option takes priority. If a direction does not
        have a distance and the "distance" input is not provided, then no buffering
        is applied to that direction. The directions refer to the sides of the
        matrix of data values as follows:

        left   | values[ :,  0]
        right  | values[ :, -1]
        top    | values[ 0,  :]
        bottom | values[-1,  :]

        self.buffer(..., *, pixels=True)
        Indicates that the units of the input distances are in pixels, rather than
        the units of the raster's transform. When using this option, the raster
        no longer requires an affine transformation. Non-integer pixel buffers
        are rounded up to the next highest integer.

        self.buffer(..., *, nodata)
        self.buffer(..., *, nodata, casting)
        Specifies a NoData value to use for the buffer pixels. You may only use
        this option when the raster does not already have a NoData value - raises a
        ValueError if this is not the case. The buffered raster will have its NoData
        value set to this value. By default, raises an error if the NoData value
        cannot be safely casted to the dtype of the raster. Use the casting option
        to implement different casting requirements.
        ----------
        Inputs:
            distance: A default buffer for all sides of the raster.
            left: A buffer for the left side of the raster
            right: A buffer for the right side of the raster
            top: A buffer for the top of the raster
            bottom: A buffer for the bottom of the raster
            pixels: True if input distances are in units of pixels. False (default)
                if input distances are in the units of the transform.
            nodata: A NoData value used for buffered pixels when a raster does not
                already have a NoData value.
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
        """

        # Require at least 1 buffer. Require a transform if units are not pixels
        # Parse and validate the NoData value
        if all_nones(distance, left, right, top, bottom):
            raise ValueError("You must specify at least 1 buffering distance.")
        elif not pixels and self.transform is None:
            raise RasterTransformError(
                f"Cannot buffer {self.name} because it does not have an affine transformation. "
                "Note that a transform is not required when buffering using the 'pixels' option."
            )
        nodata = self._parse_nodata(nodata, casting)

        # Get the number of pixels in each buffer, then buffer the raster
        buffers = self._compute_buffers(distance, left, right, top, bottom, pixels)
        self._buffer(buffers, nodata)

    def _compute_buffers(
        self, distance: Any, left: Any, right: Any, top: Any, bottom: Any, pixels: bool
    ) -> dict[str, int]:
        """Validates buffering distances and returns a dict with the number of
        buffer pixels in each direction"""

        # Get the default buffering distance
        if distance is None:
            distance = 0
        else:
            distance = self._validate_distance(distance, "distance")

        # Get the conversion factor between input distances and pixels
        if pixels:
            dx = 1
            dy = 1
        else:
            dx, dy = self.resolution

        # Get the number of pixels to buffer in each direction
        buffers = Raster._edge_dict(left, right, top, bottom, dx, dy)
        for name, (buffer, spacing) in buffers.items():
            buffer = self._validate_buffer(buffer, name, default=distance)
            npixels = ceil(buffer / spacing)
            buffers[name] = npixels

        # Require at least 1 nonzero buffer
        if not any(buffers.values()):
            raise ValueError("At least one direction must have a non-zero buffer")
        return buffers

    def _buffer(self, buffers: dict[str, int], nodata: ScalarArray) -> None:
        "Buffers the raster by the specified number of pixels in each direction"

        # Preallocate the buffered array
        nrows = self.height + buffers["top"] + buffers["bottom"]
        ncols = self.width + buffers["left"] + buffers["right"]
        values = np.full((nrows, ncols), nodata, self.dtype)

        # Copy the current array into the buffered array
        rows = slice(buffers["top"], buffers["top"] + self.height)
        cols = slice(buffers["left"], buffers["left"] + self.width)
        values[rows, cols] = self._values

        # Compute the new transform and update the object
        if self.transform is None:
            transform = None
        else:
            left = self.left - self.dx * buffers["left"]
            top = self.top - self.dy * buffers["top"]
            transform = Transform.build(self.dx, self.dy, left, top)
        self._finalize(values, self._crs, transform, nodata, "safe")

    #####
    # Reprojection
    #####

    @staticmethod
    def _validate_resampling(resampling: Any) -> str:
        "Validates a requested resampling option"

        allowed = [method.name for method in Resampling]
        allowed.remove("gauss")
        method = validate.option(resampling, "resampling", allowed)
        return getattr(Resampling, method)

    @staticmethod
    def _alignment(
        icrs: CRS,
        fcrs: CRS,
        shape: shape2d,
        stransform: Affine,
        ttransform: Affine,
    ) -> tuple[shape2d, Affine]:
        "Computes the shape and affine transform of an aligned reprojection"

        # Convert affine matrices to transform objects
        stransform = Transform(stransform)
        ttransform = Transform(ttransform)

        # Get the bounds of the raster in the new projection.
        # The final aligned bounds must fully contain these bounds.
        left, bottom, right, top = rasterio.warp.transform_bounds(
            icrs,
            fcrs,
            stransform.left,
            stransform.bottom(shape[0]),
            stransform.right(shape[1]),
            stransform.top,
        )

        # Orient the bounds in the same orientation as the target transform
        if np.sign(stransform.dx) != np.sign(ttransform.dx):
            left, right = right, left
        if np.sign(stransform.dy) != np.sign(ttransform.dy):
            top, bottom = bottom, top

        # Compute an affine transform with an aligned top-left corner
        left = Raster._align_edge(ttransform.dx, ttransform.left, left)
        top = Raster._align_edge(ttransform.dy, ttransform.top, top)
        transform = Transform.build(ttransform.dx, ttransform.dy, left, top)

        # Calculate the shape of the aligned reprojection
        nrows = Raster._axis_length(top, bottom, ttransform.yres)
        ncols = Raster._axis_length(left, right, ttransform.xres)
        shape = (nrows, ncols)
        return shape, transform

    @staticmethod
    def _align_edge(delta: float, tedge: float, redge: float) -> float:
        """
        Locates an aligned left or top edge
        ----------
        delta: The dx or dy spacing (positive or negative) of the axis
        tedge: The location of the edge in the template transform
        redge: The edge of the reprojected raster's data values
        """

        distance = redge - tedge
        npixels = floor(distance / delta)
        return tedge + npixels * delta

    @staticmethod
    def _axis_length(edge1: float, edge2: float, resolution: float) -> float:
        distance = abs(edge1 - edge2)
        return ceil(distance / resolution)

    def reproject(
        self,
        template: Optional[Self] = None,
        *,
        crs: Optional[CRS] = None,
        transform: Optional[Affine] = None,
        nodata: Optional[scalar] = None,
        casting: str = "safe",
        resampling: str = "nearest",
        num_threads: int = 1,
        warp_mem_limit: scalar = 0,
    ) -> None:
        """
        Reprojects a raster to match the spatial characteristics of another raster
        ----------
        self.reproject(template)
        Reprojects the current raster to match the spatial characteristics of a
        template raster. The current raster is projected into the same CRS,
        resolution, and grid alignment as the template. If either raster does not
        have a CRS, then the rasters are assumed to have the same CRS. If either
        raster does not have an affine transform, then the rasters are assumed to
        have the same resolution and grid alignment.

        If the raster is projected outside of its current bounds, then the reprojected
        pixels outside the bounds are set to the raster's NoData value. Raises an
        error if the raster does not have a NoData value, although see below for
        a syntax to resolve this. If resampling is required, uses nearest-neighbor
        interpolation by default, but see below for additional resampling options.

        self.reproject(..., *, crs)
        self.reproject(..., *, transform)
        Specify the crs and/or transform used to reproject the alignment. Note that
        the transform is used to determine reprojected resolution and grid alignment.
        If you provide one of these keyword options in addition to the 'template'
        input, then the keyword value will take priority.

        self.reproject(..., *, nodata)
        self.reproject(..., *, nodata, casting)
        Specfies a NoData value to use for reprojection. You can only provide this
        option if the raster does not already have a NoData value. Otherwise raises
        an Exception. The NoData value must be castable to the dtype of the raster
        being reprojected. By default, only safe casting is allowed. Use the
        casting option to enforce different casting rules.

        self.reproject(..., *, resampling)
        Specifies the interpolation algorithm used for resampling. The default
        is nearest-neighbor interpolation. Other options include bilinear, cubic,
        cubic-spline, Lanczos-windowed, average, and mode resampling. Additional
        algorithms may be available depending on your GDAL installation. See the
        rasterio documentation for additional details on resampling algorithms
        and their requirements:
        https://rasterio.readthedocs.io/en/stable/api/rasterio.enums.html#rasterio.enums.Resampling

        self.reproject(..., *, num_threads)
        self.reproject(..., *, warp_mem_limit)
        Specify the number of worker threads and/or memory limit when reprojecting
        a raster. Reprojection can be computationally expensive, but increasing
        the number of workers and memory limit can speed up this process. These
        options are passed directly to rasterio, which uses them to implement the
        reprojection. Note that the units of warp_mem_limit are MB. By default,
        uses 1 worker and 64 MB.
        ----------
        Inputs:
            template: A template Raster that defines the CRS, resolution, and
                grid alignment of the reprojected raster.
            crs: The CRS to use for reprojection. Overrides the template CRS
            transform: The transform used to determe the resolution and grid
                alignment of the reprojection. Overrides the template transform.
            nodata: A NoData value for rasters that do not already have a NoData value
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
            resampling: The resampling interpolation algorithm to use. Options
                include 'nearest' (default), 'bilinear', 'cubic', 'cubic_spline',
                'lanczos', 'average', and 'mode'. Depending on the GDAL installation,
                the following options may also be available: 'max', 'min', 'med',
                'q1', 'q3', 'sum', and 'rms'.
            num_threads: The number of worker threads used to reproject the raster
            warp_mem_limit: The working memory limit (in MB) used to reproject
        """

        # Require at least 1 reprojection parameter
        if all_nones(template, crs, transform):
            raise ValueError(
                "The template, crs, and transform inputs cannot all be None."
            )

        # Validate and parse projection metadata
        crs, transform = self._validate_spatial(crs, transform)
        template = self._parse_template(
            template, "template raster", {"crs": crs, "transform": transform}
        )
        crs = self._parse_metadatas(
            self.crs, template["crs"], default=CRS.from_epsg(4326)
        )
        transform = self._parse_metadatas(
            self.transform, template["transform"], default=Affine.identity()
        )
        nodata = self._parse_nodata(nodata, casting)
        resampling = Raster._validate_resampling(resampling)

        # Compute the shape and transform for an aligned reprojection
        shape, transform["aligned"] = Raster._alignment(
            crs["source"],
            crs["template"],
            self.shape,
            transform["source"],
            transform["template"],
        )

        # Convert boolean data to uint8 (rasterio does not accept bools)
        if self.dtype == bool:
            isbool = True
            source = self.values.astype("uint8")
        else:
            isbool = False
            source = self.values

        # Reproject the array
        values = np.empty(shape, dtype=source.dtype)
        rasterio.warp.reproject(
            source=source,
            destination=values,
            src_crs=crs["source"],
            dst_crs=crs["template"],
            src_transform=transform["source"],
            dst_transform=transform["aligned"],
            src_nodata=self.nodata,
            dst_nodata=nodata,
            resampling=resampling,
            num_threads=num_threads,
            warp_mem_limit=warp_mem_limit,
        )

        # Restore boolean arrays and update the object
        if isbool:
            values = values.astype(bool)
        self._finalize(values, crs["template"], transform["aligned"], nodata, "unsafe")

    #####
    # Clipping
    #####

    _bounds = dict[str, float]
    _ClippedValues = tuple[MatrixArray, ScalarArray | None]

    @staticmethod
    def _parse_bounds(
        clipped: _EdgeDict,
        source: BoundingBox,
        ttransform: Transform,
        template: Self | None,
    ) -> None:
        """Parses and validates bounds from keyword options, a bounding template
        raster, and the current raster. Updates a dict of clipped bounds in-place"""

        # If there's a template raster, get its bounds in the same orientation
        # as the current raster
        if template is not None:
            left_min = source.left <= source.right
            top_max = source.top >= source.bottom
            template = ttransform.oriented_bounds(template.shape, left_min, top_max)

        # Parse the clipping bounds from the keyword options and template raster
        for edge, (bound, resolution) in clipped.items():
            current = getattr(source, edge)
            if bound is None:
                if template is None:
                    bound = current
                else:
                    bound = getattr(template, edge)

            # Validate the bound
            name = f"The {edge} clipping bound"
            bound = validate.scalar(bound, name, dtype=real)
            validate.defined(bound, name)
            clipped[edge] = float(bound)

        # Ensure the bounds are in the same orientation as the source raster
        Raster._validate_orientation(clipped, source, "left", "right")
        Raster._validate_orientation(clipped, source, "bottom", "top")

    @staticmethod
    def _validate_orientation(
        clipped: _bounds, source: BoundingBox, min_edge: str, max_edge: str
    ) -> None:
        """Checks that clipping bounds along an axis (1) do not match, and
        (2) have the same orientation as the source raster"""

        # Get the values on the (ordered) minimum and maximum edges
        min_clip = clipped[min_edge]
        max_clip = clipped[max_edge]
        min_source = getattr(source, min_edge)
        max_source = getattr(source, max_edge)

        # Prevent matching clipping bounds
        if min_clip == max_clip:
            raise ValueError(
                f"The {min_edge} and {max_edge} clipping bounds are equal (value = {min_clip})."
            )

        # Get the two orientations
        corder = min_clip <= max_clip
        sorder = min_source <= max_source

        # Informative error if the orientations don't match
        if corder != sorder:
            gtlt = (">", "<")
            raise ValueError(
                f"The orientation of the {min_edge} and {max_edge} clipping bounds "
                f"({min_edge} = {min_clip} {gtlt[corder]} {max_clip} = {max_edge}) "
                f"does not match the orientation of the current raster "
                f"({min_edge} = {min_source} {gtlt[sorder]} {max_source} = {max_edge}). "
                f"Try swapping the {min_edge} and {max_edge} clipping bounds."
            )

    def clip(
        self,
        bounds: Optional[Self] = None,
        *,
        left: Optional[scalar] = None,
        bottom: Optional[scalar] = None,
        right: Optional[scalar] = None,
        top: Optional[scalar] = None,
        nodata: Optional[scalar] = None,
        casting: str = "safe",
    ) -> None:
        """
        clip  Clips a raster to the indicated bounds
        ----------
        self.clip(bounds)
        Clips a raster to the spatial bounds of a second raster. If a clipping
        bound does not align with the edge of a pixel, clips the bound to the
        nearest pixel edge. Both rasters must have the same CRS - if either
        raster does not have a CRS, then they are assumed to be the same. Similarly,
        if either raster does not have a transform, then the two rasters are
        assumed to have the same transform.

        If the clipping bounds include areas outside the current raster, then pixels
        in these areas are set to the raster's NoData value. Raises an error if
        this occurs, but the raster does not have a NoData value. (And see below
        for a syntax to resolve this).

        self.clip(..., *, left)
        self.clip(..., *, bottom)
        self.clip(..., *, right)
        self.clip(..., *, top)
        Specifies the clipping bounds for a particular edge of the raster. The
        "bounds" input is not required if at least one of these keyword options is
        provided. If the "bounds" input is not provided, then any unspecified edges
        are set to their current bounds, so are not clipped. If "bounds" is provided,
        then any keyword bounds will take priority over the bounds of the clipping
        raster. As with the "bounds" input, keyword bounds must align with the
        current raster's grid.

        Keyword bounds must also match the orientation of the current raster. For
        example, if the raster's left spatial coordinate is less than its right
        coordinate, then the left clipping bound must be less than the right
        clipping bound. But if the raster's left spatial coordinate is greater
        than its right coordinate, then the left clipping bound must be greater
        than the right clipping bound. Same for the top and bottom edges.

        self.clip(..., *, nodata)
        self.clip(..., *, nodata, casting)
        Specfies a NoData value to use when clipping a raster outside of its
        original bounds. You can only provide this option if the raster does not
        already have a NoData value, otherwise raises an Exception. The NoData
        value must be castable to the dtype of the raster being reprojected. By
        default, only safe casting is allowed. Use the casting option to enable
        different casting rules.
        ----------
        Inputs:
            bounds: A second raster whose bounds will be used to clip the current raster
            left: The bound for the left edge of the clipped raster
            right: The bound for the right edge of the clipped raster
            bottom: The bound for the bottom edge of the clipped raster
            top: The bound for the top edge of the clipped raster
            nodata: A NoData value for rasters that do not have a NoData value
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
        """

        # Require at least 1 clipping input.
        if all_nones(bounds, left, bottom, right, top):
            raise ValueError(
                "The bounds, left, bottom, right, and top inputs cannot all be None."
            )

        # Validate the optional bounding raster and get its spatial metadata.
        template = Raster._parse_template(
            bounds, "bounds", {"crs": None, "transform": None}
        )

        # Require the same CRS
        if (
            (self.crs is not None)
            and (template["crs"] is not None)
            and (self.crs != template["crs"])
        ):
            raise RasterCrsError(
                "Cannot clip because the 'bounds' raster has a different CRS than "
                "the current raster"
            )

        # Require at least one transform
        if (self.transform is None) and (template["transform"] is None):
            if bounds is None:
                raise RasterTransformError(
                    "Cannot clip because the raster does not have a transform and there "
                    "is no bounding raster."
                )
            else:
                raise RasterTransformError(
                    "Cannot clip because neither the raster nor the bounding raster "
                    "has a transform."
                )

        # Get the transforms for the current raster and clipping domain.
        transform = Raster._parse_metadatas(self.transform, template["transform"])
        stransform = Transform(transform["source"])
        ttransform = Transform(transform["template"])

        # Get the bounds, step size, and resolution of the current (source) raster
        source = stransform.bounds(self.shape)
        width, height = stransform.resolution

        # Parse and validate the bounds for the clipped raster
        clipped = self._edge_dict(left, right, top, bottom, width, height)
        self._parse_bounds(clipped, source, ttransform, bounds)

        # Get the data array and NoData for the clipped raster
        values, nodata = self._clipped_values(stransform, clipped, nodata, casting)

        # Get the final CRS and new transform. Update the raster
        crs = self.crs
        if crs is None:
            crs = template["crs"]
        transform = Transform.build(
            stransform.dx, stransform.dy, clipped["left"], clipped["top"]
        )
        self._finalize(values, crs, transform, nodata, casting)

    def _clipped_values(
        self, stransform: Transform, clipped: _bounds, nodata: Any, casting: Any
    ) -> _ClippedValues:
        "Returns the data array and nodata for a clipped raster"

        # Get the indices for the clipped array
        xs = [clipped["left"], clipped["right"]]
        ys = [clipped["top"], clipped["bottom"]]
        rows, cols = rasterio.transform.rowcol(stransform.affine, xs, ys, op=round)

        # Clip to an interior or exterior portion of the current array, as needed
        if (
            rows[0] >= 0
            and rows[1] <= self.height
            and cols[0] >= 0
            and cols[1] <= self.width
        ):
            return self._clip_interior(rows, cols)
        else:
            return self._clip_exterior(rows, cols, nodata, casting)

    def _clip_interior(
        self, rows: tuple[int, int], cols: tuple[int, int]
    ) -> _ClippedValues:
        """Clips a raster to bounds completely within the current bounds
        Uses a view of the current base array and inherits NoData (which may be None)"""

        rows = slice(rows[0], rows[1])
        cols = slice(cols[0], cols[1])
        values = self._values[rows, cols]
        return values, self.nodata

    def _clip_exterior(
        self, rows: tuple[int, int], cols: tuple[int, int], nodata: Any, casting: Any
    ) -> _ClippedValues:
        """Clips a raster to an area at least partially outside its current bounds.
        Creates a new base array and requires a NoData value"""

        # Require a NoData value
        nodata = self._parse_nodata(nodata, casting)

        # Preallocate a new base array
        nrows = rows[1] - rows[0]
        ncols = cols[1] - cols[0]
        values = np.full((nrows, ncols), nodata, dtype=self.dtype)

        # Get the complete set of indices for the final clipped array
        crows = np.arange(0, nrows)
        ccols = np.arange(0, ncols)

        # Get the same indices, but in the indexing scheme of the source array.
        srows = np.arange(rows[0], rows[1])
        scols = np.arange(cols[0], cols[1])

        # Limit indices to real pixels, then copy pixels between arrays
        srows, crows = self._clip_indices(srows, crows, self.width)
        scols, ccols = self._clip_indices(scols, ccols, self.height)
        values[crows, ccols] = self._values[srows, scols]
        return values, nodata

    @staticmethod
    def _clip_indices(
        current: VectorArray, clipped: VectorArray, nmax: int
    ) -> tuple[slice, slice]:
        """
        Returns the indices of retained pixels in the current and clipped arrays
        ----------
        current: Indices of complete clipped raster within source array
        clipped: Indices of complete clipped raster within clipped array
        nmax: The length of the dimension in the source array
        """

        # Limit the indices to those that correspond to pixels in the current raster
        keep = (current >= 0) & (current < nmax)
        current = current[keep]
        clipped = clipped[keep]

        # Convert to slices. Use empty slice if there is no overlap
        if current.size == 0:
            current = slice(0, 0)
            clipped = current
        else:
            current = slice(current[0], current[-1] + 1)
            clipped = slice(clipped[0], clipped[-1] + 1)
        return current, clipped


#####
# Type Hints
#####
RasterInput = str | Path | rasterio.DatasetReader | MatrixArray | Raster | PyshedsRaster
