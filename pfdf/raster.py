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

from math import ceil
from pathlib import Path
from typing import Any, Literal, Optional, Self

import numpy as np
import rasterio
import rasterio.features
import rasterio.transform
from affine import Affine
from pysheds.sview import Raster as PyshedsRaster
from pysheds.sview import ViewFinder

from pfdf._utils import align, all_nones, clip, no_nones, nodata, real, window
from pfdf._utils.features import FeatureFile
from pfdf._utils.nodata import NodataMask
from pfdf._validate import raster as validate
from pfdf.errors import (
    CRSError,
    MissingCRSError,
    MissingTransformError,
    RasterCRSError,
    RasterShapeError,
    RasterTransformError,
)
from pfdf.projection import CRS, BoundingBox, Transform, _crs
from pfdf.typing import (
    BooleanArray,
    Casting,
    MatrixArray,
    Pathlike,
    RealArray,
    ScalarArray,
    scalar,
    shape2d,
    vector,
)


class Raster:
    """
    Raster  Manages raster datasets and metadata
    ----------
    The Raster class is used to manage raster datasets and metadata within the pfdf
    package. Each Raster object represents a raster dataset and provides properties
    to retrieve the raster's data grid and spatial metadata. The class provides
    various factory functions to load such datasets from different formats. The
    class also includes a number of preprocessing methods, which can be used to
    prepare a dataset for assessment. Finally, all pfdf routines that compute
    rasters will return the new raster as a Raster object. Use the "save" method
    to save these rasters to file.
    ----------
    FOR USERS:
    Object Creation:
        __init__        - Returns a raster object for a supported raster input
        from_array      - Creates a Raster object from a numpy array
        from_file       - Creates a Raster from a file-based dataset
        from_rasterio   - Creates a Raster from a rasterio.DatasetReader object
        from_pysheds    - Creates a Raster from a pysheds.sview.Raster object

    From Vector Features:
        from_points     - Creates a Raster from point / multi-point features
        from_polygons   - Creates a Raster from polygon / multi-polygon features

    Data Properties:
        name            - An optional name to identify the raster
        values          - The data values associated with a raster
        dtype           - The dtype of the raster array
        nodata          - The NoData value associated with the raster
        nodata_mask     - The NoData mask for the raster
        data_mask       - The valid data mask for the raster

    Shape Properties:
        shape           - The shape of the raster array
        size            - The size (number of elements) in the raster array
        height          - The number of rows in the raster array
        width           - The number of columns in the raster array

    Spatial Properties:
        crs             - The coordinate reference system associated with the raster
        transform       - The affine Transform used to map raster pixels to spatial coordinates
        bounds          - A BoundingBox with the spatial coordinates of the raster's edges

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
        _set_metadata       - Sets the CRS, transform, and NoData attributes
        _from_array         - Builds a raster from an array without copying

    Metadata Parsing:
        _parse_template     - Parses crs and transform from a template and keyword options
        _parse_nodata       - Parses nodata from the current raster and keyword input
    """

    # User input type hints
    CRSInput = CRS | Self | int | str | dict | Any
    TransformInput = Transform | Self | dict | list | tuple | Affine
    BoundsInput = BoundingBox | Self | dict | list | tuple
    RasterInput = (
        Self | str | Path | rasterio.DatasetReader | MatrixArray | PyshedsRaster
    )
    ResolutionInput = scalar | tuple[scalar, scalar] | vector | Self | Transform

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

    @nodata.setter
    def nodata(self, nodata: scalar) -> None:
        if self._nodata is not None:
            raise ValueError(
                "Cannot set the NoData value because the raster already has a NoData value."
            )
        self._nodata = validate.nodata(nodata, casting_="safe", dtype=self.dtype)

    @property
    def nodata_mask(self) -> BooleanArray:
        return nodata.mask(self.values, self.nodata)

    @property
    def data_mask(self) -> BooleanArray:
        return ~self.nodata_mask

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
        height, width = self.shape
        return height * width

    ##### CRS

    @property
    def crs(self) -> CRS:
        return self._crs

    @crs.setter
    def crs(self, crs: CRSInput) -> None:
        if self._crs is not None:
            raise ValueError(
                "Cannot set the CRS because the raster already has a CRS. "
                "See the 'reproject' method to change a raster's CRS."
            )
        self._crs = validate.crs(crs)

    ##### Transform

    @property
    def transform(self) -> Transform:
        if self._transform is None:
            return None
        else:
            transform = self._transform.todict()
            transform["crs"] = self.crs
            return Transform.from_dict(transform)

    @transform.setter
    def transform(self, transform: TransformInput) -> None:
        "Sets the Raster Transform if there is none"

        # Setter only allowed for missing metadata
        if self.transform is not None:
            raise ValueError(
                "Cannot set the transform because the raster already has a transform. "
                "See the 'reproject' method to change a raster's transform."
            )

        # Validate transform. Require same CRS
        transform = validate.transform(transform)
        crs, reproject = self._parse_crs(transform)
        if reproject:
            raise CRSError(
                f"Cannot set the transform because the CRS of the Transform "
                f"({transform.crs.name}) is different from the Raster CRS ({crs.name})"
            )
        self._finalize(self.values, crs, transform, self.nodata)

    def _pixel(self, method, meters, needs_y: bool = True):
        "Returns a pixel geometry property"
        if self.transform is None:
            return None
        method = getattr(self.transform, method)
        if needs_y:
            _, y = self.bounds.center
            return method(meters, y)
        else:
            return method(meters)

    def dx(self, meters: bool = False):
        return self._pixel("dx", meters)

    def dy(self, meters: bool = False):
        return self._pixel("dy", meters, needs_y=False)

    def resolution(self, meters: bool = False):
        return self._pixel("resolution", meters)

    def pixel_area(self, meters: bool = False):
        return self._pixel("pixel_area", meters)

    def pixel_diagonal(self, meters: bool = False):
        return self._pixel("pixel_diagonal", meters)

    @property
    def affine(self):
        if self.transform is None:
            return None
        else:
            return self.transform.affine

    ##### Bounds

    @property
    def bounds(self) -> BoundingBox:
        if self.transform is None:
            return None
        else:
            bounds = self.transform.bounds(*self.shape).todict()
            bounds["crs"] = self.crs
            return BoundingBox.from_dict(bounds)

    @bounds.setter
    def bounds(self, bounds: BoundsInput) -> None:
        # Setter only allowed for no transform
        if self.transform is not None:
            raise ValueError(
                "Cannot set the bounds because the raster already has bounds. See "
                "the 'clip' method to change a raster's bounds."
            )

        # Validate bounds. Convert to transform and set
        bounds = validate.bounds(bounds)
        self.transform = bounds.transform(*self.shape)

    def _bound(self, name):
        if self.bounds is None:
            return None
        else:
            return getattr(self.bounds, name)

    @property
    def left(self):
        return self._bound("left")

    @property
    def right(self):
        return self._bound("right")

    @property
    def top(self):
        return self._bound("top")

    @property
    def bottom(self):
        return self._bound("bottom")

    @property
    def center(self):
        return self._bound("center")

    @property
    def orientation(self):
        return self._bound("orientation")

    ##### Misc metadata

    def override(
        self,
        *,
        crs: Optional[CRSInput] = None,
        transform: Optional[TransformInput] = None,
        nodata: Optional[scalar] = None,
        casting: Casting = "safe",
    ):
        """
        Overrides current metadata values
        ----------
        self.override(*, crs)
        self.override(*, transform)
        self.override(*, nodata)
        self.override(*, nodata, casting)
        Overrides current metadata values and replaces them with new values. The
        new values must still be valid metadata. For example, the new CRS must be
        convertible to a rasterio CRS object, the nodata value must be a scalar,
        etc. By default, requires safe nodata casting - use the casting input to
        specify a different casting rule.

        IMPORTANT: Only use this method if you know what you're doing! This command
        replaces existing metadata values, but does not ensure that those values
        are correct. For example, overriding the CRS **will not** reproject
        the raster. It will merely replace the CRS metadata. As such, incorrect
        usage of this command will result in rasters with incorrect georeferencing
        and/or incorrect data masks. Most users should not use this method.
        ----------
        Inputs:
            crs: New CRS metadata for the raster
            transform: A new affine transform for the raster
            nodata: A new NoData value for the raster
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
        """

        if crs is None:
            crs = self.crs
        if transform is None:
            transform = self.transform
        if nodata is None:
            nodata = self.nodata
        self._finalize(self.values, crs, transform, nodata, casting)

    #####
    # Low-level initialization
    #####

    @staticmethod
    def _create(
        name: Any,
        values: Any,
        crs: Any,
        transform: Any,
        nodata: Any,
        casting: Any,
        isbool: bool,
    ) -> Self:
        "Creates a new raster from the provided values and metadata"

        raster = Raster(None, name)
        raster._finalize(values, crs, transform, nodata, casting, isbool)
        return raster

    def _finalize(
        self,
        values: Any,
        crs: Any,
        transform: Any,
        nodata: Any,
        casting: Any = "safe",
        isbool: bool = False,
    ) -> None:
        """Validates and sets array values and metadata. Casts NoData to the dtype
        of the raster. Converts affine to Transform object. Optionally converts
        array boolean (after validating bool conversion). Locks array values as
        read-only
        """

        # Validate array values, metadata, and NoData casting
        self._values = validate.matrix(values, self.name, dtype=real)
        crs, transform, nodata = validate.metadata(
            crs, transform, nodata, casting, self.dtype
        )

        # Optionally convert to boolean
        if isbool:
            self._values = validate.boolean(values, "a boolean raster", ignore=nodata)
            nodata = np.bool_(False)

        # Strip CRS from the transform
        if transform is not None:
            transform = transform.todict()
            transform["crs"] = None
            transform = Transform.from_dict(transform)

        # Set metadata and lock the array values. This prevents users from altering
        # the base array when using views of the data values
        self._set_metadata(crs, transform, nodata)
        self._values.setflags(write=False)

    def _match(self, template: Self) -> None:
        "Copies the attributes from a template raster to the current raster"
        self._values = template._values
        self._set_metadata(template._crs, template._transform, template._nodata)

    def _set_metadata(
        self, crs: CRS, transform: Transform, nodata: ScalarArray
    ) -> None:
        "Sets the CRS, transform, and NoData attributes"
        self._crs = crs
        self._transform = transform
        self._nodata = nodata

    #####
    # Object Creation
    #####

    def __init__(
        self,
        raster: Optional[RasterInput] = None,
        name: Optional[str] = None,
        isbool: bool = False,
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

        Raster(..., isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the data values. The newly created raster will have a bool
        dtype and values, and its NoData value will be set to False. When using
        this option, all data pixels in the raster must be equal to 0 or 1.
        NoData pixels in the raster will be converted to False, regardless of
        their value.

        Raster()
        Returns an empty raster object. The attributes of the raster are all set
        to None. This syntax is typically not useful for users, and is instead
        intended for developers.
        ----------
        Inputs:
            raster: A supported raster dataset
            name: A name for the input raster. Defaults to 'raster'
            isbool: True indicates that the raster represents a boolean array.
                False (default) leaves the raster as its original dtype.

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
        self._transform: Optional[Transform] = None

        # Set name
        if name is None:
            name = "raster"
        self.name = name

        # If no inputs were provided, just return the empty object
        if raster is None:
            return

        # Otherwise, build an object using a factory
        elif isinstance(raster, (str, Path)):
            raster = Raster.from_file(raster, name, isbool=isbool)
        elif isinstance(raster, rasterio.DatasetReader):
            raster = Raster.from_rasterio(raster, name, isbool=isbool)
        elif isinstance(raster, PyshedsRaster):
            raster = Raster.from_pysheds(raster, name, isbool=isbool)
        elif isinstance(raster, np.ndarray):
            raster = Raster.from_array(raster, name, isbool=isbool)

        # Error if the input is not recognized
        elif not isinstance(raster, Raster):
            raise TypeError(
                f"{self.name} is not a recognized type. Allowed types are: "
                "str, pathlib.Path, rasterio.DatasetReader, 2d numpy.ndarray, "
                "pfdf.raster.Raster, and pysheds.sview.Raster objects."
            )

        # Set attributes to the values from the factory object
        self._match(raster)
        self._finalize(
            raster._values, raster._crs, raster._transform, raster._nodata, "unsafe"
        )

    @staticmethod
    def from_file(
        path: Pathlike,
        name: Optional[str] = None,
        *,
        driver: Optional[str] = None,
        band: int = 1,
        isbool: bool = False,
        bounds: Optional[BoundsInput] = None,
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

        Raster.from_file(..., *, window)
        Only loads data from a windowed subset of the saved dataset. This option is
        useful when you only need a small portion of a very large raster, and
        limits the amount of data loaded into memory. You should also use this
        option whenever a saved raster is larger than your computer's RAM.

        The "window" input indicates a rectangular portion of the saved dataset
        that should be loaded. If the window extends beyond the bounds of the
        dataset, then the dataset will be windowed to the relevant bound, but no
        further. The window may either be a Raster object, or a vector with 4
        elements. If a raster, then this method will load the portion of the dataset
        that contains the bounds of the window raster.

        If the window is a vector, then the elements should indicate, in order:
        (1) The index of the left-most column, (2) The index of the upper-most row,
        (3) Width -- number of columns, and (4) Height -- number of rows.
        All four elements must be positive integers. Width and height cannot be zero.

        Note: When filling a window, this command will first read the entirety of one
        or more data chunks from the file. As such, the total memory usage will
        temporarily exceed the memory needed to hold just the window. If a raster
        doesn't use chunks (rare, but possible), then the entire raster will be
        read into memory before filling the window. In practice, it's important
        to chunk the data you use for applications.
        ----------
        Inputs:
            path: A path to a file-based raster dataset
            name: An optional name for the raster
            band: The raster band to read. Uses 1-indexing and defaults to 1
            driver: A file format to use to read the raster, regardless of extension
            isbool: True to convert the raster to a boolean array, with nodata=False.
                False (default) to leave the raster as the original dtype.
            window: Only loads a subset of the saved raster. Either a Raster, or
                a vector of 4 positive integers.

        Outputs:
            Raster: A Raster object for the file-based dataset
        """

        # Validate inputs
        path = validate.input_path(path, "path")
        if driver is not None:
            validate.type(driver, "driver", str, "string")
        validate.type(band, "band", int, "int")
        if bounds is not None:
            bounds = validate.bounds(bounds)

        # Open file. Get metadata
        with rasterio.open(path) as file:
            crs = file.crs
            transform = file.transform
            nodata = file.nodata

            # Build window if available. Load values
            if bounds is not None:
                bounds, crs, transform = window.build(file, bounds)
            values = file.read(band, window=bounds)

        # Return Raster, optionally converting to boolean
        return Raster._create(name, values, crs, transform, nodata, "unsafe", isbool)

    @staticmethod
    def from_rasterio(
        reader: rasterio.DatasetReader,
        name: Optional[str] = None,
        *,
        band: int = 1,
        isbool: bool = False,
        bounds: Optional[BoundsInput] = None,
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

        Raster.from_rasterio(..., *, isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the file data values. The newly created raster will have a bool
        dtype and values, and its NoData value will be set to False. When using
        this option, all data pixels in the original file must be equal to 0 or
        1. NoData pixels in the file will be converted to False, regardless of
        their value.

        Raster.from_rasterio(..., *, window)
        Only loads data from a windowed subset of the saved dataset. This option is
        useful when you only need a small portion of a very large raster, and
        limits the amount of data loaded into memory. You should also use this
        option whenever a saved raster is larger than your computer's RAM.

        The "window" input indicates a rectangular portion of the saved dataset
        that should be loaded. If the window extends beyond the bounds of the
        dataset, then the dataset will be windowed to the relevant bound, but no
        further. The window may either be a Raster object, or a vector with 4
        elements. If a raster, then this method will load the portion of the dataset
        that contains the bounds of the window raster.

        If the window is a vector, then the elements should indicate, in order:
        (1) The index of the left-most column, (2) The index of the upper-most row,
        (3) Width -- number of columns, and (4) Height -- number of rows.
        All four elements must be positive integers. Width and height cannot be zero.

        Note: When filling a window, this command will first read the entirety of one
        or more data chunks from the file. As such, the total memory usage will
        temporarily exceed the memory needed to hold just the window. If a raster
        doesn't use chunks (rare, but possible), then the entire raster will be
        read into memory before filling the window. In practice, it's important
        to chunk the data you use for applications.
        ----------
        Inputs:
            reader: A rasterio.DatasetReader associated with a raster dataset
            name: An optional name for the raster. Defaults to "raster"
            band: The raster band to read. Uses 1-indexing and defaults to 1
            isbool: True to convert the raster to a boolean array, with nodata=False.
                False (default) to leave the raster as the original dtype.
            window: Limits loaded values to a subset of the saved raster. Either
                a Raster, or a vector of 4 positive integers.

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
        return Raster.from_file(
            path, name, isbool=isbool, driver=reader.driver, band=band, bounds=bounds
        )

    @staticmethod
    def from_pysheds(
        sraster: PyshedsRaster, name: Optional[str] = None, isbool: bool = False
    ) -> Self:
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

        Raster.from_pysheds(..., *, isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the file data values. The newly created raster will have a bool
        dtype and values, and its NoData value will be set to False. When using
        this option, all data pixels in the original file must be equal to 0 or
        1. NoData pixels in the file will be converted to False, regardless of
        their value.
        ----------
        Inputs:
            sraster: The pysheds.sview.Raster object used to create the new Raster
            name: An optional name for the raster. Defaults to "raster"
            isbool: True to convert the raster to a boolean array, with nodata=False.
                False (default) to leave the raster as the original dtype.

        Outputs:
            Raster: The new Raster object
        """

        validate.type(
            sraster, "input raster", PyshedsRaster, "pysheds.sview.Raster object"
        )
        crs = CRS.from_wkt(sraster.crs.to_wkt())
        values = np.array(sraster, copy=True)
        return Raster._create(
            name, values, crs, sraster.affine, sraster.nodata, "unsafe", isbool
        )

    @staticmethod
    def _from_array(
        array: MatrixArray,
        *,
        crs: Any,
        transform: Any,
        nodata: Any,
        bounds: Optional[BoundingBox] = None,
    ) -> Self:
        "Builds a Raster from optional metadata and a validated array without copying"
        raster = Raster._create(
            None, array, crs, transform, nodata, casting="safe", isbool=False
        )
        if bounds is not None:
            raster.clip(bounds)
        return raster

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
        isbool: bool = False,
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

        Raster.from_array(..., *, isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the file data values. The newly created raster will have a bool
        dtype and values, and its NoData value will be set to False. When using
        this option, all data pixels in the original file must be equal to 0 or
        1. NoData pixels in the file will be converted to False, regardless of
        their value.
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
            isbool: True to convert the raster to a boolean array, with nodata=False.
                False (default) to leave the raster as the original dtype.

        Outputs:
            Raster: A raster object for the array-based raster dataset
        """

        # Validate metadata. Parse from template and keyword options
        crs, transform, nodata = validate.metadata(crs, transform, nodata, casting)
        crs, transform = Raster._parse_template(
            spatial, "spatial template", crs, transform
        )

        # Copy array and build the object
        values = np.array(array, copy=True)
        return Raster._create(
            name,
            values,
            crs,
            transform,
            nodata,
            casting,
            isbool,
        )

    #####
    # From vector features
    #####

    @staticmethod
    def from_points(
        path: Pathlike,
        *,
        field: Optional[str] = None,
        fill: Optional[scalar] = None,
        resolution: ResolutionInput = 1,
        meters: bool = False,
        bounds: Optional[BoundsInput] = None,
        layer: Optional[int | str] = None,
        driver: Optional[str] = None,
        encoding: Optional[str] = None,
    ) -> Self:
        """
        Creates a Raster from a set of point/multi-point features
        ----------
        Raster.from_points(path)
        Raster.from_points(path, *, layer)
        Returns a boolean raster derived from the input point features. Pixels
        containing a point are set to True. All other pixels are set to False.
        The CRS of the output raster is inherited from the input feature file.
        The default resolution of the output raster is 1 (in the units of the
        CRS), although see below for options for other resolutions. The bounds of
        the raster will be the minimal bounds required to contain all input points
        at the indicated resolution.

        The contents of the input file should resolve to a FeatureCollection of
        Point and/or MultiPoint geometries. If the file contains multiple
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

        Raster.from_points(..., *, field)
        Raster.from_points(..., *, field, fill)
        Builds the raster using the indicated field of the point-feature data properties.
        The specified field must exist in the data properties, and must be an int
        or float type. The output raster will have a float dtype, regardless of
        the type of the data field, and the NoData value will be NaN. Pixels that
        contain a point are set to the value of the data field for that point.
        If a pixel contains multiple points, then the pixel's value will match
        the data field of the final point in the set. By default, all pixels not
        in a point are set as Nodata (NaN). Use the "fill" option to specify a
        default data value for these pixels instead.

        Raster.from_points(path, *, resolution)
        Raster.from_points(path, *, resolution, meters=True)
        Specifies the resolution of the output raster. The resolution may be a
        scalar positive number, a 2-tuple of such numbers, a Transform, or a Raster
        object. If a scalar, indicates the resolution of the output raster (in the
        units of the CRS) for both the X and Y axes. If a 2-tuple, the first element
        is the X-axis resolution and the second element is the Y-axis. If a Raster
        or a Transform, uses the associated resolution. Raises an error if a Raster
        object does not have a Transform.

        If resolution does not have an associated CRS, then the resolution values
        are interpreted as the base unit of the CRS in the vector feature file.
        Set meters=True to interpret resolution values as meters instead. Note that
        the "meters" option is ignored if the input resolution has a CRS.

        Raster.from_points(..., *, bounds)
        Only loads vector features that intersect with the indicated bounds. The
        returned raster is also clipped to these bounds. This option can be useful
        when you only need a Raster covering a subset of a much larger dataset.

        Raster.from_points(..., *, driver)
        Raster.from_points(..., *, encoding)
        Specifies the file format driver and encoding used to read the Points
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
            path: The path to a Point or MultiPoint feature file
            field: The name of a data property field used to set pixel values.
                The data field must have an int or float type.
            fill: A default fill value for rasters built using a data field.
                Ignored if field is None.
            resolution: The desired resolution of the output raster
            layer: The layer of the input file from which to load the point geometries
            driver: The file-format driver to use to read the Point feature file
            encoding: The encoding of the Point feature file

        Outputs:
            Raster: The point-derived raster. Pixels that contain a point are set
                either to True, or to the value of a data field. All other pixels
                are either a fill value or NoData (False or NaN).
        """

        # Open file. Validate. Parse raster settings
        resolution, bounds = validate.feature_options(resolution, bounds)
        with FeatureFile("point", path, layer, driver, encoding) as file:
            features, crs, transform, shape, dtype, nodata, fill = file.process(
                field, fill, resolution, meters, bounds
            )

        # Pad shape by 1 to account for edge points
        nrows, ncols = shape
        shape = (nrows + 1, ncols + 1)

        # Build the raster array
        raster = np.full(shape, fill, dtype)
        for geometry, value in features:
            coords = geometry["coordinates"]
            coords = np.array(coords).reshape(-1, 2)
            rows, cols = rasterio.transform.rowcol(
                transform.affine, xs=coords[:, 0], ys=coords[:, 1]
            )
            raster[rows, cols] = value

        # Build the final object, clipping as needed
        return Raster._from_array(
            raster, crs=crs, transform=transform, nodata=nodata, bounds=bounds
        )

    @staticmethod
    def from_polygons(
        path: Pathlike,
        *,
        field: Optional[str] = None,
        fill: Optional[scalar] = None,
        resolution: ResolutionInput = 1,
        meters: bool = False,
        bounds: Optional[BoundsInput] = None,
        layer: Optional[int | str] = None,
        driver: Optional[str] = None,
        encoding: Optional[str] = None,
    ) -> Self:
        """
        Creates a Raster from a set of polygon/multi-polygon features
        ----------
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

        Raster.from_polygons(..., *, resolution)
        Raster.from_polygons(..., *, resolution, meters=True)
        Specifies the resolution of the output raster. The resolution may be a
        scalar positive number, a 2-tuple of such numbers, a Transform, or a Raster
        object. If a scalar, indicates the resolution of the output raster (in the
        units of the CRS) for both the X and Y axes. If a 2-tuple, the first element
        is the X-axis resolution and the second element is the Y-axis. If a Raster
        or a Transform, uses the associated resolution. Raises an error if a Raster
        object does not have a Transform.

        If resolution does not have an associated CRS, then the resolution values
        are interpreted as the base unit of the CRS in the vector feature file.
        Set meters=True to interpret resolution values as meters instead. Note that
        the "meters" option is ignored if the input resolution has a CRS.

        Raster.from_polygons(..., *, bounds)
        Only loads vector features that intersect with the indicated bounds. The
        returned raster is also clipped to these bounds. This option can be useful
        when you only need a Raster covering a subset of a much larger dataset.

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
            meters: How to interpret resolution units when the resolution lacks a
                CRS. True to to interpret resolution as meters. False (default)
                to interpret resolution in the base unit of the vector file CRS.
            layer: The layer of the input file from which to load the polygon geometries
            driver: The file-format driver to use to read the polygon feature file
            encoding: The encoding of the polygon feature file

        Outputs:
            Raster: The polygon-derived raster. Pixels whose centers are in a
                polygon are set either to True, or to the value of a data field.
                All other pixels are either a fill value or NoData (False or NaN).
        """

        # Open file. Validate. Parse raster settings
        resolution, bounds = validate.feature_options(resolution, bounds)
        with FeatureFile("polygon", path, layer, driver, encoding) as file:
            features, crs, transform, shape, dtype, nodata, fill = file.process(
                field, fill, resolution, meters, bounds
            )

        # Rasterize the polygon features. Use uint8 for bool as needed
        if dtype == bool:
            dtype = "uint8"
        raster = rasterio.features.rasterize(
            features,
            out_shape=shape,
            transform=transform.affine,
            fill=fill,
            dtype=dtype,
        )

        # Convert to boolean as needed and build final Raster
        if field is None:
            raster = raster.astype(bool)
        return Raster._from_array(
            raster, crs=crs, transform=transform, nodata=nodata, bounds=bounds
        )

    #####
    # Metadata Parsing
    #####

    def _parse_crs(self, other):
        "Parses final CRS and reprojection needs from a metadata object"
        crs = _crs.parse(self.crs, other.crs)
        reproject = _crs.different(crs, other.crs)
        return crs, reproject

    def _parse_nodata(
        self, nodata: Any, casting: Any, optional: bool = False
    ) -> ScalarArray:
        "Parses a Nodata value from the current raster and a keyword input"

        # None is allowed if NoData is optional
        if all_nones(self.nodata, nodata) and optional:
            return None

        # Otherwse require exactly 1 NoData value
        elif all_nones(self.nodata, nodata):
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
            return validate.nodata(nodata, casting, self.dtype)

    @staticmethod
    def _parse_template(template, name, crs, transform):
        """Parses CRS and transfrom from a template raster and keyword options.
        Prioritizes keywords, but uses template metadata as backup if available"""

        if template is not None:
            validate.type(template, name, Raster, "Raster object")
            if crs is None:
                crs = template.crs
            if transform is None:
                transform = template.transform
        return crs, transform

    @staticmethod
    def _parse_src_dst(source, dest, default):
        "Parses source and destination values"
        if no_nones(source, dest):
            return source, dest
        elif all_nones(source, dest):
            return default, default
        elif source is None and dest is not None:
            return dest, dest
        else:
            return source, source

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

    def validate(self, raster: RasterInput, name: str) -> Self:
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

        # CRS
        if raster.crs is None:
            raster._crs = self.crs
        elif raster.crs != self.crs:
            raise RasterCRSError(
                f"The CRS of the {raster.name} ({raster.crs}) does not "
                f"match the CRS of the {self.name} ({self.crs})."
            )

        # Transform
        if raster.transform is None:
            raster._transform = self._transform
        elif raster.transform != self.transform:
            raise RasterTransformError(
                f"The affine transformation of the {raster.name}:\n{raster.transform}\n"
                f"does not match the transform of the {self.name}:\n{self.transform}"
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

        # Get the affine transform
        affine = None
        if self.transform is not None:
            affine = self.transform.affine

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
            transform=affine,
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
            metadata["affine"] = self.transform.affine
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
        self._finalize(data, self.crs, self.transform, nodata=None)

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
        min = validate.data_bound(min, "min", self.dtype)
        max = validate.data_bound(max, "max", self.dtype)
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
        self._finalize(values, self.crs, self.transform, nodata)

    #####
    # Spatial Preprocessing
    #####

    def buffer(
        self,
        distance: Optional[scalar] = None,
        units: Literal["default", "meters", "pixels"] = "default",
        *,
        left: Optional[scalar] = None,
        bottom: Optional[scalar] = None,
        right: Optional[scalar] = None,
        top: Optional[scalar] = None,
        nodata: Optional[scalar] = None,
        casting: Casting = "safe",
    ) -> None:
        """
        Buffers the current raster by a specified minimum distance
        ----------
        self.buffer(distance)
        self.buffer(distance, units='meters')
        self.buffer(distance, units='pixels')
        Buffers the current raster by the specified minimum distance and returns the
        buffered raster. Buffering adds a number of NoData pixels to each edge of the
        raster's data value matrix, such that the number of pixels is *as least* as long
        as the specified distance. Raises an error if the raster does not have a
        NoData value, but see below for a syntax to resolve this.

        Note that the number of pixels added to the x and y axes can differ if
        these axes have different resolutions. Also note that if the buffering
        distance is not a multiple of an axis's resolution, then the buffering
        distance along that axis will be longer than the input distance. (The
        discrepancy will be whatever distance is required to round the buffering
        distance up to a whole number of pixels). Raises an error if the raster
        does not have an affine transformation, but use the units='pixels' option
        (see below) to relax this requirement.

        The input distance must be positive. By default, this distance is interpreted
        in the default units of the raster's CRS. Set units='meters' to provide
        a buffering distance in meters instead, or set units='pixels' to indicate
        the number of pixels that should be buffered along each edge. Non-integer
        pixel distances will be rounded up to the next highest integer.

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

        Note that edge-specific buffers are interpreted using whatever units were
        indicated by the "units" option (default CRS unit, meters, or pixels).

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
            units: 'default' to provide buffers in the default unit of the raster's
                CRS, 'meters' to provide buffers in meters, or 'pixels' to provide
                buffers in pixels
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

        # Validate buffers and units
        units = validate.option(units, "units", allowed=["default", "meters", "pixels"])
        if units != "pixels" and self.transform is None:
            raise MissingTransformError(
                f"Cannot buffer {self.name} because it does not have an affine transform. "
                'Note that a transform is not required when buffering with the units="pixels" option.'
            )
        elif units == "meters" and self.crs is None:
            raise MissingCRSError(
                f"Cannot convert buffering distances from meters because {self.name} "
                "does not have a CRS."
            )
        buffers = validate.buffers(distance, left, bottom, right, top)
        nodata = self._parse_nodata(nodata, casting)

        # Build conversion dict from axis units to pixels
        if units != "pixels":
            xres, yres = self.resolution()
            resolution = {"left": xres, "right": xres, "top": yres, "bottom": yres}

        # Convert buffers to a whole number of pixels
        if units == "meters":
            buffers = _crs.buffers_from_meters(self, buffers)
        for name, buffer in buffers.items():
            if units != "pixels":
                buffer = buffer / resolution[name]
            buffers[name] = ceil(buffer)

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
            dx, dy = self.dx(), self.dy()
            left = self.left - dx * buffers["left"]
            top = self.top - dy * buffers["top"]
            transform = Transform(dx, dy, left, top)
        self._finalize(values, self.crs, transform, nodata)

    def clip(
        self,
        bounds: BoundsInput,
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
            nodata: A NoData value for rasters that do not have a NoData value
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
        """

        # Require a transform
        if self.transform is None:
            raise MissingTransformError(
                f"Cannot clip {self.name} because it does not have an affine Transform."
            )

        # Parse NoData, bounds, and CRS. Reproject bounds if needed
        nodata = self._parse_nodata(nodata, casting, optional=True)
        bounds = validate.bounds(bounds)
        crs, reproject = self._parse_crs(bounds)
        if reproject:
            bounds = bounds.reproject(self.crs)

        # Orient bounds, clip array, compute transform, and update raster
        bounds = bounds.orient(self.orientation)
        values = clip.values(self.values, bounds, self.affine, nodata)
        transform = Transform(self.dx(), self.dy(), bounds.left, bounds.top)
        self._finalize(values, crs, transform, nodata)

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

        # Require at least 1 reprojection parameter and a transform
        if all_nones(template, crs, transform):
            raise ValueError(
                "The template, crs, and transform inputs cannot all be None."
            )
        elif self.transform is None:
            raise MissingTransformError(
                f"Cannot reproject {self.name} because it does not have an affine Transform."
            )

        # Initial validation
        resampling = validate.resampling(resampling)
        nodata = self._parse_nodata(nodata, casting)

        # Parse CRS and validate transform
        crs, transform = validate.spatial(crs, transform)
        crs, transform = self._parse_template(
            template, "template raster", crs, transform
        )
        src_crs, crs = self._parse_src_dst(self.crs, crs, default=CRS(4326))
        src_transform, transform = self._parse_src_dst(
            self.transform, transform, default=Transform(1, 1, 0, 0)
        )

        # Compute transform and shape of aligned reprojection
        transform = transform._format(crs, self.bounds)
        transform, shape = align.reprojection(src_crs, crs, self.bounds, transform)

        # Convert boolean data to uint8 (rasterio does not accept bools)
        source = self.values
        if self.dtype == bool:
            source = source.astype("uint8")

        # Reproject the array
        values = np.empty(shape, dtype=source.dtype)
        rasterio.warp.reproject(
            source=source,
            destination=values,
            src_crs=src_crs,
            dst_crs=crs,
            src_transform=src_transform.affine,
            dst_transform=transform.affine,
            src_nodata=self.nodata,
            dst_nodata=nodata,
            resampling=resampling,
            num_threads=num_threads,
            warp_mem_limit=warp_mem_limit,
        )

        # Restore boolean arrays and update the object
        if self.dtype == bool:
            values = values.astype(bool)
        self._finalize(values, crs, transform, nodata)


#####
# Type Hints
#####
RasterInput = str | Path | rasterio.DatasetReader | MatrixArray | Raster | PyshedsRaster
