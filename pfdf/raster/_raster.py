"""
A class for working with raster datasets
----------
This module provides the "Raster" class, which pfdf uses to manage raster datasets.
The class can acquire raster values and metadata from a variety of formats,
and all computed rasters are returned as Raster objects. (And please see the docstring
of the Raster class for additional details).
----------
Class:
    Raster      - Class that manages raster datasets and metadata
"""

from __future__ import annotations

import typing
from math import floor
from pathlib import Path

import numpy as np
import rasterio
import rasterio.features
import rasterio.transform
from pysheds.sview import Raster as PyshedsRaster
from pysheds.sview import ViewFinder

import pfdf._validate.core as cvalidate
import pfdf.raster._utils.validate as rvalidate
from pfdf import raster as _raster
from pfdf._utils import merror, nodata, real, rowcol
from pfdf._utils.nodata import NodataMask
from pfdf.errors import (
    MissingNoDataError,
    RasterCRSError,
    RasterShapeError,
    RasterTransformError,
)
from pfdf.raster._utils import clip, factory

if typing.TYPE_CHECKING:
    from typing import Any, Optional, Self

    from affine import Affine

    from pfdf.projection import CRS, BoundingBox, Transform
    from pfdf.raster import Raster, RasterMetadata
    from pfdf.typing.core import (
        BooleanArray,
        BufferUnits,
        Casting,
        MatrixArray,
        Pathlike,
        RealArray,
        ScalarArray,
        Units,
        operation,
        scalar,
        timeout,
    )
    from pfdf.typing.raster import (
        BoundsInput,
        CRSInput,
        RasterInput,
        ResolutionInput,
        Template,
        TransformInput,
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
    **PROPERTIES**
    Data Array:
        name            - An optional name to identify the raster
        values          - The data values associated with a raster
        dtype           - The dtype of the raster array
        nbytes          - Total number of bytes used by the data array

    NoData Value:
        nodata          - The NoData value associated with the raster
        nodata_mask     - The NoData mask for the raster
        data_mask       - The valid data mask for the raster

    Shape:
        shape           - The shape of the raster array
        size            - The size (number of elements) in the raster array
        height          - The number of rows in the raster array
        width           - The number of columns in the raster array

    CRS:
        crs             - The coordinate reference system associated with the raster
        crs_units       - The units of the CRS X and Y axes
        crs_units_per_m - The number of CRS units per meter along the X and Y axes
        utm_zone        - The UTM zone CRS that contains the raster's center point

    Transform:
        transform       - A Transform object for the raster
        affine          - An affine.Affine object for the raster's transform

    BoundingBox:
        bounds          - A BoundingBox object for the raster
        left            - The spatial coordinate of the raster's left edge
        bottom          - The spatial coordinate of the raster's bottom edge
        right           - The spatial coordinate of the raster's right edge
        top             - The spatial coordinate of the raster's top edge
        center          - The (X, Y) coordinate of the raster's center
        center_x        - The X coordinate of the center
        center_y        - The Y coordinate of the center
        orientation     - The Cartesian quadrant of the bounding box

    **METHODS**
    Object Creation:
        __init__        - Returns a raster object for a supported raster input
        from_file       - Creates a Raster from a file-based dataset
        from_url        - Creates a Raster for the dataset at the indicated URL
        from_rasterio   - Creates a Raster from a rasterio.DatasetReader object
        from_array      - Creates a Raster object from a numpy array
        from_pysheds    - Creates a Raster from a pysheds.sview.Raster object

    From Vector Features:
        from_points     - Creates a Raster from point / multi-point features
        from_polygons   - Creates a Raster from polygon / multi-polygon features

    Pixel Geometries:
        dx              - Change in X-axis coordinate when moving one pixel right
        dy              - Change in Y-axis coordinate when moving one pixel down
        resolution      - Returns the resolution of the raster pixels
        pixel_area      - Returns the area of one pixel
        pixel_diagonal  - Returns the length of a pixel diagonal

    Metadata Setters:
        ensure_nodata   - Sets a NoData value if the Raster does not already have one
        override        - Overrides metadata fields with new values

    Comparisons:
        __eq__          - True if the second object is a Raster with the same values, nodata, transform, and crs
        validate        - Checks that a second raster has a compatible shape, transform, and crs

    IO:
        __repr__        - Returns a string summarizing the Raster
        save            - Saves a raster dataset to file
        copy            - Creates a copy of the current Raster
        as_pysheds      - Returns a Raster as a pysheds.sview.Raster object

    Preprocessing:
        __getitem__     - Returns a Raster object for the indexed portion of a data array
        fill            - Fills a raster's NoData pixels with the indicated data value
        find            - Returns a boolean raster indicating pixels that match specified values
        set_range       - Forces a raster's data pixels to fall within the indicated range
        buffer          - Buffers the edges of a raster by specified distances
        reproject       - Reprojects a raster to match a specified CRS, resolution, and grid alignment
        clip            - Clips a raster to the specified bounds

    **INTERNAL**
    Attributes:
        _name               - Identifying name
        _values             - Saved data values
        _nodata             - NoData value
        _crs                - Coordinate reference system
        _transform          - Affine Transform, stripped of its CRS

    Projection Metadata:
        _pixel              - Returns a pixel geometry property
        _bound              - Returns a BoundingBox property

    Object creation:
        _create             - Creates a new raster from provided values and metadata
        _finalize           - Validate/sets attributes, casts nodata, locks array, strips CRS from transform
        _match              - Copies the attributes of a template raster to the current raster
        _set_metadata       - Sets the CRS, transform, and NoData attributes

    Vector Features:
        _from_features      - Creates Raster from a feature array, clipping bounds as needed
    """

    #####
    # Object creation
    #####

    def __init__(
        self,
        raster: Optional[RasterInput] = None,
        name: Optional[str] = None,
        isbool: bool = False,
        ensure_nodata: bool = True,
        default_nodata: Optional[scalar] = None,
        casting: str = "safe",
    ) -> None:
        """
        Creates a new Raster object
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

        Raster(..., *, default_nodata)
        Raster(..., *, default_nodata, casting)
        Raster(..., *, ensure_nodata=False)
        Specifies additional options for NoData values. By default, if the raster
        file does not have a NoData value, then this routine will set a default
        NoData value based on the dtype of the raster. Set ensure_nodata=False to
        disable this behavior. Alternatively, you can use the "default_nodata" option
        to specify a different default NoData value. The default nodata value should
        be safely castable to the raster dtype, or use the "casting" option to
        specify other casting rules.
        ----------
        Inputs:
            raster: A supported raster dataset
            name: A name for the input raster. Defaults to 'raster'
            isbool: True indicates that the raster represents a boolean array.
                False (default) leaves the raster as its original dtype.
            ensure_nodata: True (default) to assign a default NoData value based
                on the raster dtype if the file does not record a NoData value.
                False to leave missing NoData as None.
            default_nodata: The default NoData value to use if the raster file is
                missing one. Overrides any default determined from the raster's dtype.
            casting: The casting rule to use when converting the default NoData
                value to the raster's dtype.

        Outputs:
            Raster: The Raster object for the dataset
        """

        # Initialize attributes
        self._values: MatrixArray = None
        self._metadata: RasterMetadata = _raster.RasterMetadata(name=name)

        # If no inputs were provided, just return the empty object
        if raster is None:
            return

        # Otherwise, build an object using a factory
        elif isinstance(raster, (str, Path)):
            raster = Raster.from_file(
                raster,
                name,
                isbool=isbool,
                ensure_nodata=ensure_nodata,
                default_nodata=default_nodata,
                casting=casting,
            )
        elif isinstance(raster, rasterio.DatasetReader):
            raster = Raster.from_rasterio(
                raster,
                name,
                isbool=isbool,
                ensure_nodata=ensure_nodata,
                default_nodata=default_nodata,
                casting=casting,
            )
        elif isinstance(raster, PyshedsRaster):
            raster = Raster.from_pysheds(raster, name, isbool=isbool)
        elif isinstance(raster, np.ndarray):
            raster = Raster.from_array(
                raster,
                name,
                isbool=isbool,
                nodata=default_nodata,
                ensure_nodata=ensure_nodata,
                casting=casting,
            )

        # Error if the input is not recognized
        elif not isinstance(raster, Raster):
            raise TypeError(
                f"{self.name} is not a recognized type. Allowed types are: "
                "str, pathlib.Path, rasterio.DatasetReader, 2d numpy.ndarray, "
                "pfdf.raster.Raster, and pysheds.sview.Raster objects."
            )

        # Set attributes to the values from the factory object
        self._copy(raster)
        self.override(name=name)

    @staticmethod
    def _create(
        values: MatrixArray,
        metadata: RasterMetadata,
        isbool: bool,
        ensure_nodata: bool,
        default_nodata: Optional[Any] = None,
        casting: Optional[Any] = None,
    ) -> Self:
        """Creates a new raster for a factory function. Implements isbool and
        ensure_nodata options before finalizing the object"""

        # Initialize empty object
        raster = Raster(None)

        # Optionally convert values to boolean. Update metadata for isbool and ensure_nodata
        if isbool:
            values = cvalidate.boolean(
                values, "a boolean raster", ignore=metadata.nodata
            )
            metadata = metadata.as_bool()
        elif ensure_nodata:
            metadata = metadata.ensure_nodata(default_nodata, casting)

        # Update and finalize the object
        raster._update(values, metadata)
        return raster

    def _update(self, values: MatrixArray, metadata: RasterMetadata) -> None:
        """Updates object with new data values. Ensures that metadata matches the array,
        then locks array values as read-only"""

        metadata = metadata.update(shape=values.shape, dtype=values.dtype)
        values.setflags(write=False)
        self._values = values
        self._metadata = metadata

    def _copy(self, template: Self) -> None:
        "Copies the attributes from a template raster to the current raster"

        self._values = template._values
        self._metadata = template._metadata

    #####
    # File factories
    #####

    @staticmethod
    def from_url(
        url: str,
        name: Optional[str] = None,
        *,
        # URL option
        check_status: bool = True,
        timeout: Optional[timeout] = 10,
        # File options
        bounds: Optional[BoundsInput] = None,
        band: int = 1,
        isbool: bool = False,
        ensure_nodata: bool = True,
        default_nodata: Optional[scalar] = None,
        casting: str = "safe",
        driver: Optional[str] = None,
    ) -> Raster:
        """
        Creates a Raster object for the dataset at the indicated URL
        ----------
        Raster.from_url(url)
        Builds a Raster object for the file at the given URL. Ultimately, this
        method uses rasterio (and thereby GDAL) to open URLs. As such, many common
        URL schemes are supported, including: http(s), ftp, s3, (g)zip, tar, etc. Note
        that although the local "file" URL scheme is theoretically supported, we
        recommend instead using "Raster.from_file" to build metadata from local
        file paths.

        If a URL follows an http(s) scheme, uses the "requests" library to check the
        URL before loading data. This check is optional (see below to disable), but
        typically provides more informative error messages when connection problems
        occur. Note that the check assumes the URL supports HEAD requests, as is the
        case for most http(s) URLs. All other URL schemes are passed directly to
        rasterio.

        After loading the URL, this method behaves nearly identically to the
        "Raster.from_file" command. Please see that command's documentation for
        details on the following options: name, bounds, band, isbool, ensure_nodata,
        default_nodata, casting, and driver.

        Raster.from_url(..., *, timeout)
        Raster.from_url(..., *, check_status=False)
        Options that affect the checking of http(s) URLs. Ignored if the URL does not
        have an http(s) scheme. The "timeout" option specifies a maximum time in
        seconds for connecting to the remote server. This option is typically a scalar,
        but may also use a vector with two elements. In this case, the first value is
        the timeout to connect with the server, and the second value is the time for the
        server to return the first byte. You can also set timeout to None, in
        which case the URL check will never timeout. This may be useful for some slow
        connections, but is generally not recommended as your code may hang indefinitely
        if the server fails to respond.

        You can disable the http(s) URL check by setting check_status=False. In this
        case, the URL is passed directly to rasterio, as like all other URL schemes.
        This can be useful if the URL does not support HEAD requests, or to limit server
        queries when you are certain the URL and connection are valid.
        ----------
        Inputs:
            url: The URL for a file-based raster dataset
            name: An optional name for the metadata. Defaults to "raster"
            timeout: A maximum time in seconds to establish a connection with
                an http(s) server
            check_status: True (default) to use "requests.head" to validate http(s) URLs.
                False to disable this check.
            bounds: A BoundingBox-like input indicating a subset of the raster
                that should be loaded.
            band: The raster band to read. Uses 1-indexing and defaults to 1
            driver: A file format to use to read the raster, regardless of extension
            isbool: True to convert the raster to a boolean array, with nodata=False.
                False (default) to leave the raster as the original dtype.
            ensure_nodata: True (default) to assign a default NoData value based
                on the raster dtype if the file does not record a NoData value.
                False to leave missing NoData as None.
            default_nodata: The default NoData value to use if the raster file is
                missing one. Overrides any default determined from the raster's dtype.
            casting: The casting rule to use when converting the default NoData
                value to the raster's dtype.

        Outputs:
            RasterMetadata: The metadata object for the raster
        """

        url, bounds = rvalidate.url(
            url, check_status, timeout, driver, band, bounds, casting
        )
        return Raster._from_file(
            url,
            driver,
            band,
            name,
            bounds,
            isbool,
            ensure_nodata,
            default_nodata,
            casting,
        )

    @staticmethod
    def from_file(
        path: Pathlike,
        name: Optional[str] = None,
        *,
        bounds: Optional[BoundsInput] = None,
        band: int = 1,
        isbool: bool = False,
        ensure_nodata: bool = True,
        default_nodata: Optional[scalar] = None,
        casting: str = "safe",
        driver: Optional[str] = None,
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
        defaults to "raster" if unset. By default, if the file does not have a
        NoData value, then selects a default value based on the dtype. See below
        for other NoData options.

        Also, by default the method will attempt to use the file extension to
        detect the file format driver used to read data from the file. Raises an
        Exception if the driver cannot be determined, but see below for options
        to explicitly set the driver. You can also use:
            >>> pfdf.utils.driver.extensions('raster')
        to return a summary of supported file format drivers, and their associated
        extensions.

        Raster.from_file(..., *, bounds)
        Only loads data from a bounded subset of the saved dataset. This option is
        useful when you only need a small portion of a very large raster, and
        limits the amount of data loaded into memory. You should also use this
        option whenever a saved raster is larger than your computer's RAM.

        The "bounds" input indicates a rectangular portion of the saved dataset
        that should be loaded. If the window extends beyond the bounds of the
        dataset, then the dataset will be windowed to the relevant bound, but no
        further. The window may be a BoundingBox, Raster, or a list/tuple/dict
        convertible to a BoundingBox object.

        Note: When filling a window, this command will first read the entirety of one
        or more data chunks from the file. As such, the total memory usage will
        temporarily exceed the memory needed to hold just the window. If a raster
        doesn't use chunks (rare, but possible), then the entire raster will be
        read into memory before filling the window. In practice, it's important
        to chunk the data you use for applications.

        Raster.from_file(..., *, band)
        Specify the raster band to read. Raster bands use 1-indexing (and not the
        0-indexing common to Python). Raises an error if the band does not exist.

        Raster.from_file(..., *, isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the file data values. The newly created raster will have a bool
        dtype and values, and its NoData value will be set to False. When using
        this option, all data pixels in the original file must be equal to 0 or
        1. NoData pixels in the file will be converted to False, regardless of
        their value.

        Raster.from_file(..., *, default_nodata)
        Raster.from_file(..., *, default_nodata, casting)
        Raster.from_file(..., *, ensure_nodata=False)
        Specifies additional options for NoData values. By default, if the raster
        file does not have a NoData value, then this routine will set a default
        NoData value based on the dtype of the raster. Set ensure_nodata=False to
        disable this behavior. Alternatively, you can use the "default_nodata" option
        to specify a different default NoData value. The default nodata value should
        be safely castable to the raster dtype, or use the "casting" option to
        specify other casting rules.

        Raster.from_file(..., *, driver)
        Specify the file format driver to use for reading the file. Uses this
        driver regardless of the file extension. You can also call:
            >>> pfdf.utils.driver.rasters()
        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on rasterio (which in turn uses GDAL/OGR)
        to read raster files, and so additional drivers may work if their
        associated build requirements are met. A complete list of driver build
        requirements is available here: https://gdal.org/drivers/raster/index.html
        ----------
        Inputs:
            path: A path to a file-based raster dataset
            name: An optional name for the raster
            bounds: A BoundingBox-like input indicating a subset of the raster
                that should be loaded.
            band: The raster band to read. Uses 1-indexing and defaults to 1
            driver: A file format to use to read the raster, regardless of extension
            isbool: True to convert the raster to a boolean array, with nodata=False.
                False (default) to leave the raster as the original dtype.
            ensure_nodata: True (default) to assign a default NoData value based
                on the raster dtype if the file does not record a NoData value.
                False to leave missing NoData as None.
            default_nodata: The default NoData value to use if the raster file is
                missing one. Overrides any default determined from the raster's dtype.
            casting: The casting rule to use when converting the default NoData
                value to the raster's dtype.

        Outputs:
            Raster: A Raster object for the file-based dataset
        """

        path, bounds = rvalidate.file(path, driver, band, bounds, casting)
        return Raster._from_file(
            path,
            driver,
            band,
            name,
            bounds,
            isbool,
            ensure_nodata,
            default_nodata,
            casting,
        )

    @staticmethod
    def _from_file(
        path_or_url: Path | str,
        driver: str | None,
        band: int,
        name: str,
        bounds: BoundingBox | None,
        isbool: bool,
        ensure_nodata: bool,
        default_nodata: Any,
        casting: str,
    ) -> Raster:
        "Builds a Raster from a file-based dataset at a path or URL"

        # Open file and get full-file metadata
        with rasterio.open(path_or_url, driver=driver) as file:
            metadata = factory.file(file, band, name)

            # Build window as needed. Load values
            if bounds is not None:
                metadata, bounds = factory.window(metadata, bounds)
            values = file.read(band, window=bounds)

        # Return Raster. Optionally convert to boolean and ensure nodata
        return Raster._create(
            values, metadata, isbool, ensure_nodata, default_nodata, casting
        )

    @staticmethod
    def from_rasterio(
        reader: rasterio.DatasetReader,
        name: Optional[str] = None,
        *,
        bounds: Optional[BoundsInput] = None,
        band: int = 1,
        isbool: bool = False,
        ensure_nodata: bool = True,
        default_nodata: Optional[scalar] = None,
        casting: str = "safe",
    ) -> Self:
        """
        Builds a raster from a rasterio.DatasetReader
        ----------
        Raster.from_rasterio(reader)
        Raster.from_rasterio(reader, name)
        Creates a new Raster object from a rasterio.DatasetReader object. Raises a
        FileNotFoundError if the associated file no longer exists. Uses the file
        format driver associated with the object to read the raster from file.
        By default, loads the data from band 1. The name input specifies an optional
        name for the new Raster object. Defaults to "raster" if unset.

        Raster.from_rasterio(..., *, bounds)
        Only loads data from a bounded subset of the saved dataset. This option is
        useful when you only need a small portion of a very large raster, and
        limits the amount of data loaded into memory. You should also use this
        option whenever a saved raster is larger than your computer's RAM.

        The "bounds" input indicates a rectangular portion of the saved dataset
        that should be loaded. If the window extends beyond the bounds of the
        dataset, then the dataset will be windowed to the relevant bound, but no
        further. The window may be a BoundingBox, Raster, or a list/tuple/dict
        convertible to a BoundingBox object.

        Note: When filling a window, this command will first read the entirety of one
        or more data chunks from the file. As such, the total memory usage will
        temporarily exceed the memory needed to hold just the window. If a raster
        doesn't use chunks (rare, but possible), then the entire raster will be
        read into memory before filling the window. In practice, it's important
        to chunk the data you use for applications.

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

        Raster.from_rasterio(..., *, default_nodata)
        Raster.from_rasterio(..., *, default_nodata, casting)
        Raster.from_rasterio(..., *, ensure_nodata=False)
        Specifies additional options for NoData values. By default, if the raster
        file does not have a NoData value, then this routine will set a default
        NoData value based on the dtype of the raster. Set ensure_nodata=False to
        disable this behavior. Alternatively, you can use the "default_nodata" option
        to specify a different default NoData value. The default nodata value should
        be safely castable to the raster dtype, or use the "casting" option to
        specify other casting rules.
        ----------
        Inputs:
            reader: A rasterio.DatasetReader associated with a raster dataset
            name: An optional name for the raster. Defaults to "raster"
            band: The raster band to read. Uses 1-indexing and defaults to 1
            isbool: True to convert the raster to a boolean array, with nodata=False.
                False (default) to leave the raster as the original dtype.
            bounds: A Raster or BoundingBox indicating a subset of the saved raster
                that should be loaded.
            ensure_nodata: True (default) to assign a default NoData value based
                on the raster dtype if the file does not record a NoData value.
                False to leave missing NoData as None.
            default_nodata: The default NoData value to use if the raster file is
                missing one. Overrides any default determined from the raster's dtype.
            casting: The casting rule to use when converting the default NoData
                value to the raster's dtype.

        Outputs:
            Raster: The new Raster object
        """

        path = rvalidate.reader(reader)
        return Raster.from_file(
            path,
            name,
            bounds=bounds,
            band=band,
            isbool=isbool,
            ensure_nodata=ensure_nodata,
            default_nodata=default_nodata,
            casting=casting,
            driver=reader.driver,
        )

    #####
    # Array factories
    #####

    @staticmethod
    def from_pysheds(
        sraster: PyshedsRaster, name: Optional[str] = None, isbool: bool = False
    ) -> Self:
        """
        Creates a Raster from a pysheds.sview.Raster object
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

        metadata = factory.pysheds(sraster, name)
        values = np.array(sraster, copy=True)
        return Raster._create(values, metadata, isbool, ensure_nodata=False)

    @staticmethod
    def from_array(
        array: MatrixArray,
        name: Optional[str] = None,
        *,
        nodata: Optional[scalar] = None,
        casting: Casting = "safe",
        crs: Optional[CRSInput] = None,
        transform: Optional[TransformInput] = None,
        bounds: Optional[BoundsInput] = None,
        spatial: Optional[Self] = None,
        isbool: bool = False,
        ensure_nodata: bool = True,
        copy: bool = True,
    ) -> Self:
        """
        Create a Raster from a numpy array
        ----------
        Raster.from_array(array, name)
        Initializes a Raster object from a raw numpy array. Infers a NoData value
        from the dtype of the array. The Transform and CRS will both be None. The raster
        name can be returned using the ".name" property and is used to identify
        the raster in error messages. Defaults to 'raster' if unset. Note that
        the new Raster object holds a copy of the input array, so changes to the
        input array will not affect the Raster, and vice-versa.

        Raster.from_array(..., *, nodata)
        Raster.from_array(..., *, nodata, casting)
        Specifies a NoData value for the raster. The NoData value will be set to
        the same dtype as the array. Raises a TypeError if the NoData value cannot
        be safely cast to this dtype. Use the casting option to change this
        behavior. Casting options are as follows:
        'no': The data type should not be cast at all
        'equiv': Only byte-order changes are allowed
        'safe': Only casts which can preserve values are allowed
        'same_kind': Only safe casts or casts within a kind (like float64 to float32)
        'unsafe': Any data conversions may be done

        Raster.from_array(..., *, spatial)
        Specifies a Raster or RasterMetadata object to use as a default spatial metadata
        template. By default, transform and crs properties from the template will be
        copied to the new raster. However, see below for a syntax to override this
        behavior.

        Raster.from_array(..., *, crs)
        Raster.from_array(..., *, transform)
        Raster.from_array(..., *, bounds)
        Specifies the crs, transform, and/or bounding box that should be associated
        with the raster. If used in conjunction with the "spatial" option, then
        any keyword options will take precedence over the metadata in the spatial
        template. You may only provide one of the transform/bounds inputs - raises
        an error if both are provided. If the CRS of a Transform or BoundingBox
        differs from the template/keyword CRS, then the Transform or BoundingBox
        is reprojected to match the other CRS.

        Raster.from_array(..., *, isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the array. The newly created raster will have a bool dtype and
        values, and its NoData value will be set to False. When using
        this option, all data pixels in the original array must be equal to 0 or
        1. NoData pixels in the array will be converted to False, regardless of
        their value.

        Raster.from_array(..., *, ensure_nodata=False)
        Disables the use of default NoData values. The returned raster's nodata
        value will be None unless the "nodata" option is specified.

        Raster.from_array(..., *, copy=False)
        By default, this command will create the Raster object from a copy of the input
        array. Set copy=False to disable copying whenever possible. (Note that a copy
        will still occur if the input is not already a numpy array). This syntax can
        save memory when initializing a raster from a very large in-memory array.
        However, changes to the base array will propagate into the Raster's data value
        matrix. As such, this syntax is not recommended for most users.
        ----------
        Inputs:
            array: A 2D numpy array whose data values represent a raster
            name: A name for the raster. Defaults to 'raster'
            nodata: A NoData value for the raster
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
            spatial: A Raster or RasterMetadata object to use as a default spatial
                metadata template for the new Raster.
            crs: A coordinate reference system for the raster
            transform: An affine transformation for the raster. Mutually exclusive
                with the "bounds" input
            bounds: A BoundingBox for the raster. Mutually exclusive with the
                "transform" input
            isbool: True to convert the raster to a boolean array, with nodata=False.
                False (default) to leave the raster as the original dtype.
            ensure_nodata: True (default) to infer a default NoData value from the
                raster's dtype when a NoData value is not provided. False to
                disable this behavior.
            copy: True (default) to build the Raster's data matrix from a copy
                of the input array. False to avoid copying whenever possible.


        Outputs:
            Raster: A raster object for the array-based raster dataset
        """

        metadata, values = factory.array(
            array, name, nodata, casting, crs, transform, bounds, spatial, copy
        )
        return Raster._create(values, metadata, isbool, ensure_nodata, nodata, casting)

    #####
    # Vector factories
    #####

    @staticmethod
    def from_points(
        path: Pathlike,
        field: Optional[str] = None,
        *,
        # Field options
        dtype: Optional[np.dtype] = None,
        field_casting: Casting = "safe",
        nodata: Optional[scalar] = None,
        casting: Casting = "safe",
        operation: Optional[operation] = None,
        # Spatial
        bounds: Optional[BoundsInput] = None,
        resolution: ResolutionInput = 10,
        units: Units = "meters",
        # File IO
        layer: Optional[int | str] = None,
        driver: Optional[str] = None,
        encoding: Optional[str] = None,
    ) -> Self:
        """
        Creates a Raster from a set of point/multi-point features
        ----------
        Raster.from_points(path)
        Returns a raster derived from the input point features. The contents of
        the input file should resolve to a FeatureCollection of Point and/or
        MultiPoint geometries (and see below if the file contains multiple layers).
        The CRS of the output raster is inherited from the input feature file.
        The default resolution of the output raster is 10 meters, although see
        below to specify other resolutions. The bounds of the raster will be the
        minimal bounds required to contain all input points at the indicated
        resolution.

        If you do not specify an attribute field, then the returned raster will
        have a boolean dtype. Pixels containing a point are set to True. All other
        pixels are set to False. See below to build the raster from an data property
        field instead.

        By default, this method will attempt to guess the intended file format and
        encoding based on the path extension. Raises an error if the format or
        encoding cannot be determined. However, see below for syntax to specify
        the driver and encoding, regardless of extension. You can also use:
            >>> pfdf.utils.driver.extensions('vector')
        to return a summary of supported file format drivers, and their associated
        extensions.

        Raster.from_points(path, field)
        Raster.from_points(..., *, dtype)
        Raster.from_points(..., *, dtype, field_casting)
        Builds the raster using one of the data property fields for the point features.
        Pixels that contain a point are set to the value of the data field for that
        point. If a pixel contains multiple points, then the pixel's value will match
        the data value of the final point in the set. Pixels that do not contain a point
        are set to a default NoData value, but see below for options to specify the
        NoData value instead.

        The indicated data field must exist in the data properties, and must have an int
        or float type. By default, the dtype of the output raster will be int32 or
        float64, as appropriate for the data field type.
        Use the "dtype" option to specify the type of the output raster instead. In this
        case, the data field values will be cast to the indicated dtype before being
        used to build the raster. By default, field values must be safely castable to
        the indicated dtype. Use the "field_casting" option to select different casting
        rules. The "dtype" and "field_casting" options are ignored if you do not specify
        a field.

        Raster.from_points(..., field, *, nodata)
        Raster.from_points(..., field, *, nodata, casting)
        Specifies the NoData value to use when building the raster from a data attribute
        field. By default, the NoData value must be safely castable to the dtype of the
        output raster. Use the "casting" option to select other casting rules. NoData
        options are ignored if you do not specify a field.

        Raster.from_points(..., field, *, operation)
        Applies the indicated function to the data field values and uses the output
        values to build the raster. The input function should accept one numeric input,
        and return one real-valued numeric output. Useful when data field values require
        a conversion. For example, you could use the following to scale Point values
        by a factor of 100:

            def times_100(value):
                return value * 100

            Raster.from_points(..., field, operation=times_100)

        Values are converted before they are validated against the "dtype" and
        "field_casting" options, so you can also use an operation to implement a custom
        conversion from data values to the output raster dtype. The operation input is
        ignored if you do not specify a field.

        Raster.from_points(..., *, bounds)
        Only uses point features contained within the indicated bounds. The returned
        raster is also clipped to these bounds. This option can be useful when
        you only need data from a subset of a much larger Point dataset.

        Raster.from_points(path, *, resolution)
        Raster.from_points(path, *, resolution, units)
        Specifies the resolution of the output raster. The resolution may be a
        scalar positive number, a 2-tuple of such numbers, a Transform, a Raster, or a
        RasterMetadata object. If a scalar, indicates the resolution of the output raster for both
        the X and Y axes. If a 2-tuple, the first element is the X-axis resolution
        and the second element is the Y-axis. If a Raster or a Transform, uses
        the associated resolution. Raises an error if a Raster object does not
        have a Transform.

        If the resolution input does not have an associated CRS, then the resolution
        values are interpreted as meters. Use the "units" option to interpret
        resolution values in different units instead. Supported units include:
        "base" (CRS/Transform base unit), "kilometers", "feet", and "miles".
        Note that this option is ignored if the input resolution has a CRS.

        Raster.from_points(..., *, layer)
        Use this option when the input feature file contains multiple layers. The
        "layer" input indicates the layer holding the relevant Point geometries.
        This may be either an integer index, or the (string) name of a layer in
        the input file.

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
            dtype: The dtype of the output raster when building from a data field
            field_casting: The type of data casting allowed to occur when converting
                data field values to a specified output dtype. Options are "no",
                "equiv", "safe" (default), "same_kind", and "unsafe".
            nodata: The NoData value for the output raster.
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
            operation: A function that should be applied to data field values before
                they are used to build the raster. Should accept one numeric input and
                return one real-valued numeric input.
            bounds: A bounding box indicating the subset of point features that
                should be used to create the raster.
            resolution: The desired resolution of the output raster
            units: Specifies the units of the resolution when the resolution input
                does not have a CRS. Options include: "base" (CRS/Transform base
                unit), "meters" (default), "kilometers", "feet", and "miles"
            layer: The layer of the input file from which to load the point geometries
            driver: The file-format driver to use to read the Point feature file
            encoding: The encoding of the Point feature file

        Outputs:
            Raster: The point-derived raster. Pixels that contain a point are set
                either to True, or to the value of a data field. All other pixels
                are NoData.
        """

        # Parse the features and metadata
        features, metadata = factory.points(
            path,
            field,
            dtype,
            field_casting,
            nodata,
            casting,
            operation,
            bounds,
            resolution,
            units,
            layer,
            driver,
            encoding,
        )

        # Initialize the raster array
        try:
            values = np.full(metadata.shape, metadata.nodata, metadata.dtype)
        except Exception as error:
            merror.features(error, "point")

        # Get the GIS coordinates for each point
        for geometry, value in features:
            coords = geometry["coordinates"]
            coords = np.array(coords).reshape(-1, 2)

            # Determine the raster index and set the index to the point's value.
            # Skip any points that fall outside the array (this can occur when a point
            # falls exactly on the right or bottom edge during windowed reading)
            rows, cols = rowcol(
                metadata.affine, xs=coords[:, 0], ys=coords[:, 1], op=floor
            )
            if max(rows) < metadata.nrows and max(cols) < metadata.ncols:
                values[rows, cols] = value

        # Build the final raster
        return Raster.from_array(
            values, copy=False, nodata=metadata.nodata, spatial=metadata
        )

    @staticmethod
    def from_polygons(
        path: Pathlike,
        field: Optional[str] = None,
        *,
        # Field options
        dtype: Optional[np.dtype] = None,
        field_casting: Casting = "safe",
        nodata: Optional[scalar] = None,
        casting: Casting = "safe",
        operation: Optional[operation] = None,
        # Spatial options
        bounds: Optional[BoundsInput] = None,
        resolution: ResolutionInput = 10,
        units: Units = "meters",
        # File IO
        layer: Optional[int | str] = None,
        driver: Optional[str] = None,
        encoding: Optional[str] = None,
    ) -> Self:
        """
        Creates a Raster from a set of polygon/multi-polygon features
        ----------
        Raster.from_polygons(path)
        Returns a raster derived from the input polygon features. The contents of
        the input file should resolve to a FeatureCollection of Polygon and/or
        MultiPolygon geometries (and see below if the file contains multiple layers).
        The CRS of the output raster is inherited from the input feature file.
        The default resolution of the output raster is 10 meters, although see
        below to specify other resolutions. The bounds of the raster will be the
        minimal bounds required to contain all input polygons at the indicated
        resolution.

        If you do not specify an attribute field, then the returned raster will
        have a boolean dtype. Pixels whose centers are in any of the polygons are
        set to True. All other pixels are set to False. See below to build the
        raster from an data property field instead.

        By default, this method will attempt to guess the intended file format and
        encoding based on the path extension. Raises an error if the format or
        encoding cannot be determined. However, see below for syntax to specify
        the driver and encoding, regardless of extension. You can also use:
            >>> pfdf.utils.driver.extensions('vector')
        to return a summary of supported file format drivers, and their associated
        extensions.

        Raster.from_polygons(path, field)
        Raster.from_polygons(..., *, dtype)
        Raster.from_polygons(..., *, dtype, field_casting)
        Builds the raster using one of the data property fields for the polygon
        features. Pixels whose centers lie within a polygon are set to the value of the
        data field for that polygon. If a pixel is in multiple polygons, then the
        pixel's value will match the data value of the final polygon in the set. Pixels
        that do no lie within a polygon are set to a default NoData value, but see below
        for options to specify the NoData value instead.

        The indicated data field must exist in the data properties, and must have an int
        or float type. By default, the dtype of the output raster will be int32 or
        float64, as appropriate..
        Use the "dtype" option to specify the type of the output raster instead. In this
        case, the data field values will be cast to the indicated dtype before being
        used to build the raster. Note that only some numpy dtypes are supported for
        building a raster from polygons. Supported dtypes are: bool, int16, int32,
        uint8, uint16, uint32, float32, and float64. Raises an error if you select a
        different dtype.
        By default, field values must be safely castable to
        the indicated dtype. Use the "field_casting" option to select different casting
        rules. The "dtype" and "field_casting" options are ignored if you do not specify
        a field.

        Raster.from_polygons(..., field, *, nodata)
        Raster.from_polygons(..., field, *, nodata, casting)
        Specifies the NoData value to use when building the raster from a data attribute
        field. By default, the NoData value must be safely castable to the dtype of the
        output raster. Use the "casting" option to select other casting rules. NoData
        options are ignored if you do not specify a field.

        Raster.from_polygons(..., field, *, operation)
        Applies the indicated function to the data field values and uses the output
        values to build the raster. The input function should accept one numeric input,
        and return one real-valued numeric output. Useful when data field values require
        a conversion. For example, you could use the following to scale Polygon values
        by a factor of 100:

            def times_100(value):
                return value * 100

            Raster.from_polygons(..., field, operation=times_100)

        Values are converted before they are validated against the "dtype" and
        "field_casting" options, so you can also use an operation to implement a custom
        conversion from data values to the output raster dtype. The operation input is
        ignored if you do not specify a field.

        Raster.from_polygons(..., *, bounds)
        Only uses polygon features that intersect the indicated bounds. The
        returned raster is also clipped to these bounds. This option can be useful
        when you only need data from a subset of a much larger Polygon dataset.

        Raster.from_polygons(..., *, resolution)
        Raster.from_polygons(..., *, resolution, units)
        Specifies the resolution of the output raster. The resolution may be a
        scalar positive number, a 2-tuple of such numbers, a Transform, or a Raster
        object. If a scalar, indicates the resolution of the output raster for both
        the X and Y axes. If a 2-tuple, the first element is the X-axis resolution
        and the second element is the Y-axis. If a Raster or a Transform, uses
        the associated resolution. Raises an error if a Raster object does not
        have a Transform.

        If the resolution input does not have an associated CRS, then the resolution
        values are interpreted as meters. Use the "units" option to interpret
        resolution values in different units instead. Supported units include:
        "base" (CRS/Transform base unit), "kilometers", "feet", and "miles".
        Note that this option is ignored if the input resolution has a CRS.

        Raster.from_polygons(..., *, layer)
        Use this option when the input feature file contains multiple layers. The
        "layer" input indicates the layer holding the relevant Polygon geometries.
        This may be either an integer index, or the (string) name of a layer in
        the input file.

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
            dtype: The dtype of the output raster when building from a data field
            field_casting: The type of data casting allowed to occur when converting
                data field values to a specified output dtype. Options are "no",
                "equiv", "safe" (default), "same_kind", and "unsafe".
            nodata: The NoData value for the output raster.
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
            operation: A function that should be applied to data field values before
                they are used to build the raster. Should accept one numeric input and
                return one real-valued numeric input.
            bounds: A bounding box indicating the subset of polygon features that
                should be used to create the raster.
            resolution: The desired resolution of the output raster
            units: Specifies the units of the resolution when the resolution input
                does not have a CRS. Options include: "base" (CRS/Transform base
                unit), "meters" (default), "kilometers", "feet", and "miles"
            layer: The layer of the input file from which to load the polygon geometries
            driver: The file-format driver to use to read the Polygon feature file
            encoding: The encoding of the Polygon feature file

        Outputs:
            Raster: The polygon-derived raster. Pixels whose centers lie within
                a polygon are set either to True, or to the value of a data field.
                All other pixels are NoData.
        """

        # Parse the features and metadata
        features, metadata = factory.polygons(
            path,
            field,
            dtype,
            field_casting,
            nodata,
            casting,
            operation,
            bounds,
            resolution,
            units,
            layer,
            driver,
            encoding,
        )

        # Use uint8 for bool as needed (rasterio does not support bool dtype)
        dtype = metadata.dtype
        if dtype == bool:
            dtype = "uint8"

        # Rasterize
        try:
            values = rasterio.features.rasterize(
                features,
                out_shape=metadata.shape,
                transform=metadata.affine,
                fill=metadata.nodata,
                dtype=dtype,
            )

        # Informative error for memory errors
        except Exception as error:
            merror.features(error, "polygon")

        # Revert to boolean as needed and build final Raster
        if field is None:
            values = values.astype(bool)
        return Raster.from_array(
            values, copy=False, nodata=metadata.nodata, spatial=metadata
        )

    #####
    # Metadata Setters
    #####

    def ensure_nodata(
        self, default: Optional[scalar] = None, casting: str = "safe"
    ) -> None:
        """
        Ensures a raster has a NoData value, setting a default value if missing
        ----------
        self.ensure_nodata()
        Checks if the raster has a NoData value. If so, no action is taken. If
        not, then sets the NoData value to a default determined by the raster's
        dtype.

        self.ensure_nodata(default)
        self.ensure_nodata(default, casting)
        Specifies the default NoData value to use if the raster does not have NoData.
        By default, the NoData value must be safely castable to the dtype of the
        raster. Use the "casting" option to select other casting rules.
        ----------
        Inputs:
            default: A default NoData value. This will override the default value
                determined automatically from the raster dtype.
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the Raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
        """

        self._metadata = self.metadata.ensure_nodata(default, casting)

    def override(
        self,
        *,
        crs: Optional[CRSInput] = None,
        transform: Optional[TransformInput] = None,
        bounds: Optional[BoundsInput] = None,
        nodata: Optional[scalar] = None,
        casting: Casting = "safe",
        name: Optional[str] = None,
    ) -> None:
        """
        Overrides current metadata values
        ----------
        self.override(*, crs)
        self.override(*, transform)
        self.override(*, bounds)
        self.override(*, nodata)
        self.override(*, nodata, casting)
        self.override(*, name)
        Overrides current metadata values and replaces them with new values. The
        new values must still be valid metadata. For example, the new CRS must be
        convertible to a rasterio CRS object, the nodata value must be a scalar,
        etc. By default, requires safe nodata casting - use the casting input to
        specify a different casting rule. Note that you can only provide one of
        the "transform" and "bounds" inputs, as these options are mutually exclusive.
        If providing transform or bounds, and its CRS does not match the current/new
        CRS, then the transform will be reprojected to the correct CRS before overriding.

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
            name: A new name for the raster
        """

        self._metadata = self.metadata.update(
            name=name,
            crs=crs,
            transform=transform,
            bounds=bounds,
            nodata=nodata,
            casting=casting,
        )

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
            raster.override(crs=self.crs)
        elif raster.crs != self.crs:
            raise RasterCRSError(
                f"The CRS of the {raster.name} ({raster.crs}) does not "
                f"match the CRS of the {self.name} ({self.crs})."
            )

        # Transform
        if raster.transform is None:
            raster.override(transform=self.transform)
        elif raster.transform != self.transform:
            raise RasterTransformError(
                f"The affine transformation of the {raster.name}:\n{raster.transform}\n"
                f"does not match the transform of the {self.name}:\n{self.transform}"
            )
        return raster

    #####
    # IO
    #####

    def __repr__(self) -> str:
        """
        Returns a string summarizing the raster
        ----------
        repr(self)
        Returns a string summarizing key information about the raster. Includes
        the shape, dtype, NoData, CRS, Transform, and BoundingBox.
        ----------
        Outputs:
            str: A string summary of the raster
        """

        return str(self.metadata).replace("RasterMetadata", "Raster", 1)

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
        path = cvalidate.output_file(path, overwrite)

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
        Returns a copy of the current Raster
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

        copy = Raster(None)
        copy._copy(self)
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

        # Get nodata or use 0 as default
        if self.nodata is None:
            nodata = np.zeros(1, self.dtype)
        else:
            nodata = self.nodata
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
        Replaces NoData pixels with the indicated value
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
        value = cvalidate.scalar(value, "fill value", dtype=real)
        value = rvalidate.casting(value, "fill value", self.dtype, casting="safe")

        # Just exit if there's not a NoData Value
        if self.nodata is None:
            return

        # Locate NoData values, copy the array, then fill the copy
        nodatas = NodataMask(self.values, self.nodata)
        data = self.values.copy()
        nodatas.fill(data, value)

        # Update the raster object
        metadata = self.metadata.fill()
        self._update(data, metadata)

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
        values = cvalidate.array(values, "values", dtype=real)
        isin = np.isin(self.values, values)

        # Also support NaN searches
        if np.any(np.isnan(values)):
            nans = np.isnan(self.values)
            isin = isin | nans
        return Raster.from_array(
            isin, crs=self.crs, transform=self.transform, nodata=False, copy=False
        )

    def set_range(
        self,
        min: Optional[scalar] = None,
        max: Optional[scalar] = None,
        fill: bool = False,
        exclude_bounds: bool = False,
    ) -> None:
        """
        Forces a raster's data values to fall within specified bounds
        ----------
        self.set_range(min, max)
        Forces the raster's data values to fall within a specified range. The min
        and max inputs specify lower and upper bounds for the range, and must be
        safely castable to the dtype of the raster. By default, uses inclusive
        bounds, although see below to use exclusive bounds instead. Data values
        that fall outside these bounds are clipped - pixels less than the lower
        bound are set to equal the bound, and pixels greater than the upper bound
        are set to equal that bound. If a bound is None, does not enforce that bound.
        Raises an error if both bounds are None.

        This method creates a copy of the raster's data values before replacing
        out-of-bounds pixels, so copies of the raster are not affected. Also, the
        method does not alter NoData pixels, even if the NoData value is outside
        of the indicated bounds.

        self.set_range(..., fill=True)
        Indicates that pixels outside the bounds should be replaced with the
        raster's NoData value, instead of being clipped to the appropriate bound.
        Raises a ValueError if the raster does not have a NoData value.

        self.set_range(..., fill=True, exclude_bounds=True)
        Indicates that the bounds should be excluded from the valid range. In this
        case, data values exactly equal to a bound are also set to NoData. This
        option is only available when fill=True.
        ----------
        Inputs:
            min: A lower bound for the raster
            max: An upper bound for the raster
            fill: If False (default), clips pixels outside the bounds to bounds.
                If True, replaces pixels outside the bounds with the NoData value
            exclude_bounds: True to consider the min and max data values as outside of
                the valid data range. False (default) to consider the min/max as
                within the valid data range. Only available when fill=True.
        """

        # Validate
        min = rvalidate.data_bound(min, "min", self.dtype)
        max = rvalidate.data_bound(max, "max", self.dtype)
        if fill and self.nodata is None:
            raise MissingNoDataError(
                f"You cannot use set_range with fill=True because the {self.name} "
                f"does not have a NoData value. Either set fill=False, or use the "
                '"ensure_nodata" command to set a NoData value for this raster.'
            )
        elif exclude_bounds and not fill:
            raise ValueError("You can only set exclusive=True when fill=True.")

        # Get the comparison operator
        if exclude_bounds:
            too_large = np.greater_equal
            too_small = np.less_equal
        else:
            too_large = np.greater
            too_small = np.less

        # Locate out-of-bounds data pixels
        values = self.values
        data = NodataMask(values, self.nodata, invert=True)
        too_large = data & too_large(values, max)
        too_small = data & too_small(values, min)

        # If filling, replace out-of-range values with NoData
        if fill:
            min = self.nodata
            max = self.nodata

        # Replace out-of-bounds values with either the closest bound, or NoData
        values = values.copy()
        too_large.fill(values, max)
        too_small.fill(values, min)
        self._update(values, self.metadata)

    #####
    # Spatial Preprocessing
    #####

    def __getitem__(self, indices: tuple[int | slice, int | slice]) -> Raster:
        """
        Returns a Raster object for the indexed portion of a raster's data array
        ----------
        self[rows, cols]
        Returns a Raster object for the indexed portion of the current object's data
        array. The "rows" input should be an index or slice, as would be applied to the
        first dimension of the current Raster's data array. The "cols" input is an int
        or slice as would be applied to the second dimension. Returns an object with
        an updated data array and spatial metadata.

        Note that this method does not alter the current object. Instead, it returns
        a new Raster object for the indexed portion of the array. The data array for the
        new object is a view of the original array - this routine does not copy data.

        This syntax has several limitations compared to numpy array indexing:
        1. Indexing is not supported when the raster shape includes a 0,
        2. Indices must select at least 1 pixel - empty selections are not supported,
        3. Slices must have a step size of 1 or None,
        4. You must provide indices for exactly 2 dimensions, and
        5. This syntax is limited to the int and slice indices available to Python
        lists. More advanced numpy indexing methods (such as boolean indices and
        ellipses) are not supported.
        ----------
        Inputs:
            rows: An index or slice for the first dimension of the raster's data array
            cols: An index or slice for the second dimension of the raster's data array

        Outputs:
            Raster: A Raster object for the indexed portion of the data array
        """

        # Get the updated metadata and array slice
        metadata, rows, cols = self.metadata.__getitem__(indices, return_slices=True)
        values = self.values[rows, cols]

        # Create the new object
        return Raster.from_array(
            values,
            name=self.name,
            nodata=self.nodata,
            spatial=metadata,
            copy=False,
        )

    def buffer(
        self,
        distance: Optional[scalar] = None,
        units: BufferUnits = "meters",
        *,
        left: Optional[scalar] = None,
        bottom: Optional[scalar] = None,
        right: Optional[scalar] = None,
        top: Optional[scalar] = None,
    ) -> None:
        """
        Buffers the current raster by a specified minimum distance
        ----------
        self.buffer(distance)
        self.buffer(distance, units)
        Buffers the current raster by the specified minimum distance. Buffering
        adds a number of NoData pixels to each edge of the raster's data value
        matrix, such that the number of pixels is *as least* as long as the
        specified distance. Raises an error if the raster does not have a NoData
        value.

        Note that the number of pixels added to the x and y axes can differ if
        these axes have different resolutions. Also note that if the buffering
        distance is not a multiple of an axis's resolution, then the actual buffer
        along that axis will be longer than the input distance. (The
        discrepancy will be whatever distance is required to round the buffering
        distance up to a whole number of pixels).

        The input distance must be positive. By default, this distance is interpreted
        as meters. Use the "units" option to provide a buffering distance in other
        units instead. Supported units include: "pixels" (the number of pixels
        to buffer along each edge), "base" (CRS/Transform base units), "meters",
        "kilometers", "feet", and "miles". Note that different units have different
        metadata requirements, as follows:

        Unit       | Required metadata
        ---------- | -----------------
        pixels     | None
        base       | Transform only
        all others | CRS and Transform

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
        indicated by the "units" option.
        ----------
        Inputs:
            distance: A default buffer for all sides of the raster.
            units: Specifies the units of the input buffers. Options include:
                "pixels", "base", "meters" (default), "kilometers", "feet", and
                "miles"
            left: A buffer for the left side of the raster
            right: A buffer for the right side of the raster
            top: A buffer for the top of the raster
            bottom: A buffer for the bottom of the raster
        """

        # Compute the metadata for the buffered raster
        edges = {"left": left, "right": right, "top": top, "bottom": bottom}
        metadata, buffers = self.metadata.buffer(
            distance, units, **edges, return_buffers=True
        )

        # Require NoData
        if self.nodata is None:
            raise MissingNoDataError(
                f"Cannot buffer {self.name} because it does not have a NoData "
                'value. See the "ensure_nodata" command to provide a NoData value '
                "for the raster."
            )

        # Preallocate the buffered array
        try:
            values = np.full(metadata.shape, self.nodata, self.dtype)
        except Exception as error:
            message = (
                f"Cannot buffer {self.name} because the buffered array is too "
                "large for memory. Try decreasing the buffering distance."
            )
            merror.supplement(error, message)

        # Copy the current array into the buffered array and update the object
        rows = slice(buffers["top"], buffers["top"] + self.nrows)
        cols = slice(buffers["left"], buffers["left"] + self.ncols)
        values[rows, cols] = self._values
        self._update(values, metadata)

    def clip(self, bounds: BoundsInput) -> None:
        """
        Clips a raster to the indicated bounds
        ----------
        self.clip(bounds)
        Clips a raster to the indicated spatial bounds. Bounds may be another
        raster, a BoundingBox object, or a dict/list/tuple representing a BoundingBox.
        If a clipping bound does not align with the edge of a pixel, clips the
        bound to the nearest pixel edge. Note that the raster must have a Transform
        in order to enable clipping.

        If the clipping bounds include areas outside the current raster, then pixels
        in these areas are set to the raster's NoData value. Raises an error if
        this occurs, but the raster does not have a NoData value.
        ----------
        Inputs:
            bounds: A Raster or BoundingBox used to clip the current raster.
        """

        metadata, rows, cols = self.metadata.clip(bounds, return_limits=True)
        values = clip.values(self.values, metadata, rows, cols)
        self._update(values, metadata)

    def reproject(
        self,
        template: Optional[Template] = None,
        *,
        crs: Optional[CRS] = None,
        transform: Optional[Affine] = None,
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
        error if the raster does not have a NoData value. If resampling is required,
        uses nearest-neighbor interpolation by default, but see below for
        additional resampling options.

        self.reproject(..., *, crs)
        self.reproject(..., *, transform)
        Specify the crs and/or transform of the reprojected raster. Note that
        the transform is used to determine reprojected resolution and grid alignment.
        If you provide one of these keyword options in addition to the 'template'
        input, then the keyword value will take priority. If using the "transform"
        input and the transform CRS does not match the template/keyword CRS, then
        the transform will be reprojected to the appropriate CRS before reprojection.

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
            resampling: The resampling interpolation algorithm to use. Options
                include 'nearest' (default), 'bilinear', 'cubic', 'cubic_spline',
                'lanczos', 'average', and 'mode'. Depending on the GDAL installation,
                the following options may also be available: 'max', 'min', 'med',
                'q1', 'q3', 'sum', and 'rms'.
            num_threads: The number of worker threads used to reproject the raster
            warp_mem_limit: The working memory limit (in MB) used to reproject
        """

        # Compute the metadata for the reprojected raster
        metadata = self.metadata.reproject(template, crs=crs, transform=transform)

        # Require NoData and validate resampling
        if self.nodata is None:
            raise MissingNoDataError(
                f"Cannot reproject {self.name} because it does not have a NoData value. "
                'See the "ensure_nodata" command to provide a NoData value for the raster.'
            )
        resampling = rvalidate.resampling(resampling)

        # Convert boolean data to uint8 (rasterio does not accept bools)
        source = self.values
        if self.dtype == bool:
            source = source.astype("uint8")

        # Preallocate
        try:
            values = np.empty(metadata.shape, dtype=source.dtype)
        except Exception as error:
            message = (
                f"Cannot reproject {self.name} because the reprojected raster "
                "is too large for memory. Try increasing the Transform's dx and dy "
                "to coarser resolution."
            )
            merror.supplement(error, message)

        # Reproject the array
        rasterio.warp.reproject(
            source=source,
            destination=values,
            src_crs=self.crs or metadata.crs,
            dst_crs=metadata.crs,
            src_transform=self.affine or metadata.affine,
            dst_transform=metadata.affine,
            src_nodata=self.nodata,
            dst_nodata=self.nodata,
            resampling=resampling,
            num_threads=num_threads,
            warp_mem_limit=warp_mem_limit,
        )

        # Restore boolean arrays and update the object
        if self.dtype == bool:
            values = values.astype(bool)
        self._update(values, metadata)

    #####
    # RasterMetadata
    #####

    @property
    def metadata(self) -> RasterMetadata:
        "Returns the metadata object for the raster"
        return self._metadata

    ##### Name

    @property
    def name(self) -> str | None:
        "Returns the identifying name"
        return self.metadata.name

    @name.setter
    def name(self, name: str) -> None:
        self.override(name=name)

    ##### Shape

    @property
    def shape(self) -> tuple[int, int]:
        "Returns the array shape"
        return self.metadata.shape

    @property
    def nrows(self) -> int:
        "Returns the number of array rows"
        return self.metadata.nrows

    @property
    def height(self) -> int:
        "Returns the number of array rows"
        return self.metadata.height

    @property
    def ncols(self) -> int:
        "Returns the number of array columns"
        return self.metadata.ncols

    @property
    def width(self) -> int:
        "Returns the number of array columns"
        return self.metadata.width

    @property
    def size(self) -> int:
        "Returns the number of array elements"
        return self.metadata.size

    ##### Data array

    @property
    def values(self) -> np.ndarray:
        "Returns a view of the data array"
        if self._values is None:
            return None
        else:
            return self._values.view()

    @property
    def dtype(self) -> np.dtype | None:
        "Returns the array dtype"
        return self.metadata.dtype

    @property
    def nbytes(self) -> int | None:
        "Total number of bytes used by the data array"
        return self.metadata.nbytes

    ##### NoData

    @property
    def nodata(self) -> ScalarArray | None:
        "Returns the NoData value"
        return self.metadata.nodata

    @nodata.setter
    def nodata(self, nodata: scalar) -> None:
        "Sets the NoData value is there is None"
        if self.nodata is not None:
            raise ValueError(
                "Cannot set the NoData value because the raster already has a NoData value."
            )
        self.override(nodata=nodata)

    @property
    def nodata_mask(self) -> BooleanArray:
        "A boolean array whose True elements are NoData pixels"
        return nodata.mask(self.values, self.nodata)

    @property
    def data_mask(self) -> BooleanArray:
        "A boolean array whose True elements are data pixels"
        return ~self.nodata_mask

    ##### CRS

    @property
    def crs(self) -> CRS | None:
        "Returns the coordinate reference system"
        return self.metadata.crs

    @crs.setter
    def crs(self, crs: CRSInput) -> None:
        "Sets the raster CRS if there is None"
        if self.crs is not None:
            raise ValueError(
                f"Cannot set the CRS because the raster already has a CRS. "
                "See the 'reproject' method to change a raster's CRS."
            )
        self.override(crs=crs)

    @property
    def crs_units(self) -> tuple[str, str] | tuple[None, None]:
        "Returns the units along the CRS's X and Y axes"
        return self.metadata.crs_units

    @property
    def crs_units_per_m(self) -> tuple[float, float] | tuple[None, None]:
        "Returns the number of CRS units per meter along the CRS's X and Y axes"
        return self.metadata.crs_units_per_m

    @property
    def utm_zone(self) -> CRS | None:
        "Returns the UTM zone CRS that contains the raster's center point"
        return self.metadata.utm_zone

    ##### Transform

    @property
    def transform(self) -> Transform:
        "Returns the affine Transform"
        return self.metadata.transform

    @transform.setter
    def transform(self, transform: TransformInput) -> None:
        "Sets the Raster Transform if there is none"
        if self.transform is not None:
            raise ValueError(
                "Cannot set the transform because the raster already has a transform. "
                "See the 'reproject' method to change a raster's transform."
            )
        self.override(transform=transform)

    def dx(self, units: Units = "meters") -> float | None:
        """
        Returns the change in the X-axis spatial coordinate when moving one pixel right
        ----------
        self.dx()
        self.dx(units)
        Returns the change in X-axis spatial coordinate when moving one pixel to
        the right. By default, returns dx in meters. Use the "units" option to
        return dx in other units. Supported units include: "base" (base unit of
        the CRS/Transform), "kilometers", "feet", and "miles".
        ----------
        Inputs:
            units: The units to return dx in. Options include: "base" (CRS/Transform
                base units), "meters" (default), "kilometers", "feet", and "miles".

        Outputs:
            float: The change in X coordinate when moving one pixel right
        """
        return self.metadata.dx(units)

    def dy(self, units: Units = "meters") -> float | None:
        """
        Returns the change in the Y-axis spatial coordinate when moving one pixel down
        ----------
        self.dy()
        self.dy(units)
        Returns the change in Y-axis spatial coordinate when moving one pixel
        down. By default, returns dy in meters. Use the "units" option to
        return dy in other units. Supported units include: "base" (base unit of
        the CRS/Transform), "kilometers", "feet", and "miles".
        ----------
        Inputs:
            units: The units to return dy in. Options include: "base" (CRS/Transform
                base units), "meters" (default), "kilometers", "feet", and "miles".

        Outputs:
            float: The change in Y coordinate when moving one pixel down
        """
        return self.metadata.dy(units)

    def resolution(self, units: Units = "meters") -> tuple[float, float] | None:
        """
        Returns the raster resolution
        ----------
        self.resolution()
        self.resolution(units)
        Returns the raster resolution as a tuple with two elements. The first
        element is the X resolution, and the second element is Y resolution. Note
        that resolution is strictly positive. By default, returns resolution in
        meters. Use the "units" option to return resolution in other units. Supported
        units include: "base" (base unit of the CRS/Transform), "kilometers",
        "feet", and "miles".
        ----------
        Inputs:
            units: The units to return resolution in. Options include:
                "base" (CRS/Transform base units), "meters" (default), "kilometers",
                "feet", and "miles".

        Outputs:
            float, float: The X and Y axis pixel resolution
        """
        return self.metadata.resolution(units)

    def pixel_area(self, units: Units = "meters") -> float | None:
        """
        Returns the area of one pixel
        ----------
        self.pixel_area()
        self.pixel_area(units)
        Returns the area of a raster pixel. By default, returns area in meters^2.
        Use the "units" option to return area in a different unit (squared).
        Supported units include: "base" (CRS/Transform base unit), "kilometers",
        "feet", and "miles".
        ----------
        Inputs:
            units: The units to return resolution in. Options include:
                "base" (CRS/Transform base units), "meters" (default), "kilometers",
                "feet", and "miles".

        Outputs:
            float: The area of a raster pixel
        """
        return self.metadata.pixel_area(units)

    def pixel_diagonal(self, units: Units = "meters") -> float | None:
        """
        Returns the length of a pixel diagonal
        ----------
        self.pixel_diagonal()
        self.pixel_diagonal(units)
        Returns the length of a pixel diagonal. By default, returns length in
        meters. Use the "units" option to return length in other units. Supported
        units include: "base" (base unit of the CRS/Transform), "kilometers",
        "feet", and "miles".
        ----------
        Inputs:
            units: The units in which to return the length of a pixel diagonal.
                Options include: "base" (CRS/Transform base units), "meters" (default),
                "kilometers", "feet", and "miles".

        Outputs:
            float: The area of a raster pixel
        """
        return self.metadata.pixel_diagonal(units)

    @property
    def affine(self) -> Affine | None:
        "Returns the affine matrix"
        return self.metadata.affine

    ##### Bounds

    @property
    def bounds(self) -> BoundingBox | None:
        "Returns the bounding box"
        return self.metadata.bounds

    @bounds.setter
    def bounds(self, bounds: BoundsInput) -> None:
        "Sets the bounding box if there is none"
        if self.bounds is not None:
            raise ValueError(
                "Cannot set the bounds because the raster already has bounds. See "
                "the 'clip' method to change a raster's bounds."
            )
        self.override(bounds=bounds)

    @property
    def left(self) -> float | None:
        "Returns the spatial coordinate of the left edge"
        return self.metadata.left

    @property
    def right(self) -> float | None:
        "Returns the spatial coordinate of the right edge"
        return self.metadata.right

    @property
    def top(self) -> float | None:
        "Returns the spatial coordinate of the top edge"
        return self.metadata.top

    @property
    def bottom(self) -> float | None:
        "Returns the spatial coordinate of the bottom edge"
        return self.metadata.bottom

    @property
    def center(self) -> tuple[float, float] | None:
        "Returns the X,Y coordinate at the center of the bounding box"
        return self.metadata.center

    @property
    def center_x(self) -> float | None:
        "Returns the X coordinate at the center of the bounding box"
        return self.metadata.center_x

    @property
    def center_y(self) -> float | None:
        "Returns the Y coordinate at the center of the bounding box"
        return self.metadata.center_y

    @property
    def orientation(self) -> int | None:
        "Returns the Cartesian orientation of the bounding box"
        return self.metadata.orientation
