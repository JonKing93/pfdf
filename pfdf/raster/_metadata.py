"""
A class to manage raster metadata
----------
This module provides the "RasterMetadata" class, which pfdf uses to manage raster
metadata. This metadata includes spatial information (such as the CRS, Transfrom, and 
BoundingBox), and also information on a raster's data array (shape, dtype, and
NoData value). The class does not record the data array directly, so can be used to
manage metadata without needing to load and/or manipulate large data arrays. Please see 
the class docstring for additional details.
----------
Class:
    RasterMetadata  - Class to manage raster metadata
"""

from __future__ import annotations

import typing
from math import ceil

import rasterio
import rasterio.transform

import pfdf._utils.nodata as _nodata
import pfdf._validate.core as cvalidate
import pfdf._validate.projection as pvalidate
import pfdf.raster._utils.validate as rvalidate
from pfdf._utils import all_nones
from pfdf._utils import buffers as _buffers
from pfdf._utils import no_nones, real, rowcol
from pfdf.errors import MissingCRSError, MissingTransformError
from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.projection import crs as _crs
from pfdf.raster._utils import align, factory, parse
from pfdf.utils.nodata import default as default_nodata

if typing.TYPE_CHECKING:
    from typing import Any, Optional

    import numpy as np
    from affine import Affine
    from pysheds.sview import Raster as PyshedsRaster

    from pfdf.raster import RasterMetadata
    from pfdf.typing.core import (
        BufferUnits,
        Casting,
        EdgeDict,
        MatrixArray,
        Pathlike,
        ScalarArray,
        Units,
        operation,
        scalar,
        shape2d,
    )
    from pfdf.typing.raster import (
        BoundsInput,
        CRSInput,
        ResolutionInput,
        Template,
        TransformInput,
    )


class RasterMetadata:
    """
    Class to manage raster metadata
    ----------
    The RasterMetadata class is used to manage metadata properties for raster datasets.
    This includes spatial metadata (CRS, Transform, BoundingBox), as well as metadata
    for a raster's data array (shape, dtype, NoData value, and optional identifying
    name). Although a RasterMetadata object records data array metadata, the class does
    not record any actual data values. As such, these objects can be used to build and
    manipulate raster metadata without needing to load or manipulate large data arrays.

    Many RasterMetadata commands are designed to mirror commands for the Raster class.
    This includes all Raster factory methods and any preprocessing methods that alter
    a raster's metadata. A given RasterMetadata factory method will return the metadata
    object that would result if the corresponding Raster factory were called with the
    same inputs. This is particularly useful for file-based datasets, as you can use the
    factory to determine the raster's metadata, without needing to load the dataset into
    memory. The factories include the "from_points" and "from_polygons" commands, so
    users can also validate and determine metadata for rasterized features, without
    needing to actually build a new data array.

    Unlike the Raster class, RasterMetadata objects are immutable, so you cannot change
    a metadata object once it's been created. Instead, use the "update" command to
    return a copy of a metadata object with altered metadata fields. All metadata fields
    are optional, although the "shape" and "name" fields will default to (0, 0) and
    "raster" if unset. You can also return updated metadata objects using various
    preprocessing methods, including: "fill", "buffer", "clip", "reproject". Each of
    these methods returns the updated metadata object that would result from applying
    the method to a theoretical data array. Advanced users may find this useful to
    inform preprocessing routines without the computational expense of manipulating
    data arrays.
    ----------
    PROPERTIES:
    Shape:
        shape           - The shape of the data array
        nrows           - The number of rows in the data array
        height          - An alias for nrows
        ncols           - The number of columns in the data array
        width           - An alias for ncols

    Data Array:
        dtype           - The numpy dtype of the data array
        nodata          - The NoData value
        name            - An identifying name for the raster dataset

    CRS:
        crs             - The coordinate reference system
        crs_units       - The unit systems used along the CRS's X and Y axes
        crs_units_per_m - The number of CRS units per meter along the X and Y axes
        utm_zone        - The CRS of the best UTM zone for the raster's center

    Transform:
        transform       - A Transform object for the raster
        affine          - An affine.Affine object for the raster

    Bounding Box:
        bounds          - A BoundingBox object for the raster
        left            - The spatial coordinate of the raster's left edge
        right           - The spatial coordinate of the raster's right edge
        top             - The spatial coordinate of the raster's top edge
        bottom          - The spatial coordinate of the raster's bottom edge
        center          - The X, Y coordinate of the raster's center
        center_x        - The X coordinate of the raster's center
        center_y        - The Y coordinate of the raster's center
        orientation     - The Cartesian quadrant containing the raster's bounding box

    METHODS:
    Object Creation:
        __init__        - Creates a RasterMetadata object for input values
        from_file       - Creates a RasterMetadata object for a file-based raster dataset
        from_rasterio   - Creates a RasterMetadata object for a rasterio.DatasetReader
        from_pysheds    - Creates a RasterMetadata object for a pysheds.sgrid.Raster object
        from_array      - Creates a RasterMetadata object for a numpy array

    Vector Features:
        from_points     - Creates a RasterMetadata object for a Point or MultiPoint feature file
        from_polygons   - Creates a RasterMetadata object for a Polygon or MultiPolygon feature file

    Pixel Geometries:
        dx              - Returns the change in X coordinate when moving one pixel right
        dy              - Returns the change in Y coordinate when moving one pixel down
        resolution      - Returns pixel resolution along the X and Y axes
        pixel_area      - Returns the area of a pixel
        pixel_diagonal  - Returns the length of a pixel diagonal

    Comparisons:
        __eq__          - True if another input is a RasterMetadata object with the same metadata
        isclose         - True if another input is a RasterMetadata object with similar metadata

    IO:
        __repr__        - Returns a string representing the metadata
        todict          - Returns a dict representing the metadata
        copy            - Returns a copy of the current metadata object

    Updated Metadata:
        __getitem__     - Returns a copy of the current metadata for the indexed portion of a data array
        update          - Returns a copy of the current metadata with updated fields
        as_bool         - Returns updated metadata suitable for a boolean data array
        ensure_nodata   - Returns updated metadata guaranteed to have a NoData value

    Preprocessing:
        fill            - Returns metadata without a NoData value
        buffer          - Returns updated metadata for a buffered raster
        clip            - Returns updated metadata for a clipped raster
        reproject       - Returns updated metadata for a reprojected raster

    Internal:
        _create         - Updates metadata for isbool and ensure_nodata factory options
        _get_locator    - Returns a finalized BoundingBox or Transform
        _pixel          - Returns a pixel geometry property
        _bound          - Returns a bounding box attribute
    """

    #####
    # Dunders / built-ins
    #####

    def __init__(
        self,
        # Data array
        shape: Optional[shape2d] = None,
        *,
        dtype: Optional[type] = None,
        nodata: Optional[scalar] = None,
        casting: str = "safe",
        # Spatial
        crs: Optional[CRSInput] = None,
        transform: Optional[TransformInput] = None,
        bounds: Optional[BoundsInput] = None,
        # Name
        name: Optional[str] = None,
    ) -> None:
        """
        Creates a new RasterMetadata object
        ----------
        RasterMetadata(shape)
        Creates a new RasterMetadata object. The shape should be the shape of a
        raster's data array. This must be a vector of two positive integers. Defaults to
        (0, 0) if not provided.

        RasterMetadata(..., *, dtype)
        RasterMetadata(..., *, nodata)
        RasterMetadata(..., *, dtype, nodata, casting)
        Specifies metadata fields that describe a raster's data array. The dtype input
        should be convertible to a real-valued numpy dtype, and the NoData value should
        be a scalar value. If you only provide a nodata value, then the dtype will be
        inherited from that value. If you provide both the dtype and nodata inputs, then
        the nodata value will be cast to the indicated dtype. By default, requires safe
        casting, but see the "casting" input to use other casting rules.

        RasterMetadata(..., *, crs)
        RasterMetadata(..., *, transform)
        RasterMetadata(..., *, bounds)
        Specifies CRS, affine transform, and/or bounding box metadata. You may only
        provide one of the "transform" and "bounds" options - these two inputs are
        mutually exclusive. You also cannot provide "bounds" metadata when the array
        shape includes 0 values. This is because the resulting Transform would require
        infinite resolution, which is invalid.

        If a transform/bounds has a CRS that differs from the "crs" input, then the
        transform/bounds will be reprojected. If you do not provide a crs, then the
        metadata will inherit any CRS from the transform/bounds. Note that the various
        preprocessing methods all require the RasterMetadata object to have a transform
        or bounding box. The "buffer" method also require a CRS when using metric or
        imperial units.

        RasterMetadata(..., *, name)
        A string specifying an identifying name. Defaults to "raster".
        ----------
        Inputs:
            shape: The shape of the raster's data array. A vector of 2 positive
                integers. Defaults to (0,0) if not set
            dtype: The dtype of a raster data array
            nodata: A NoData value. Will be cast to the dtype if a dtype is provided
            casting: The casting rule to use when casting the NoData value to the dtype.
                Options are "safe" (default), "same_kind", "no", "equiv", and "unsafe"
            crs: A coordinate reference system
            transform: An affine transform
            bounds: A bounding box
            name: A string identifying the dataset. Defaults to "raster"

        Outputs:
            RasterMetadata: The new RasterMetadata object
        """

        # Attributes
        self._shape: shape2d
        self._dtype: Optional[np.dtype] = None
        self._nodata: Optional[ScalarArray] = None
        self._crs: Optional[CRS] = None
        self._locator: Optional[Transform | BoundingBox] = None
        self._name: str = None

        # Parse name and shape from defaults and user inputs
        if name is None:
            name = "raster"
        cvalidate.type(name, "name", str, "string")
        if shape is None:
            shape = (0, 0)
        shape = rvalidate.shape2d(shape, "shape")

        # Validate data array metadata
        if dtype is not None:
            dtype = cvalidate.real_dtype(dtype, "dtype")
        if nodata is not None:
            if dtype is None:
                nodata = cvalidate.scalar(nodata, "nodata", dtype=real)
                dtype = nodata.dtype
            else:
                nodata = rvalidate.nodata(nodata, casting, dtype)

        # Validate spatial metadata
        if crs is not None:
            crs = pvalidate.crs(crs)
        if no_nones(transform, bounds):
            raise ValueError(
                'You cannot provide both "transform" and "bounds" metadata. '
                "The two inputs are mutually exclusive."
            )
        elif transform is not None:
            locator = pvalidate.transform(transform)
        elif bounds is not None:
            locator = pvalidate.bounds(bounds)
        else:
            locator = None

        # Cannot use bounds when shape is 0 because Transform would be infinite
        if isinstance(locator, BoundingBox) and any((N == 0 for N in shape)):
            raise ValueError(
                f'You cannot specify "bounds" metadata when the shape includes 0 values. '
                f'Consider using "transform" metadata instead.'
            )

        # Inherit CRS or reproject as needed. Always use bounding box to reproject.
        # Strip CRS from final locator
        if locator is not None:
            if crs is None:
                crs = locator.crs
            elif not _crs.compatible(crs, locator.crs):
                if isinstance(locator, Transform):
                    locator = locator.bounds(*shape)
                locator = locator.reproject(crs)
            locator = locator.remove_crs()

        # Set attributes
        self._shape = shape
        self._dtype = dtype
        self._nodata = nodata
        self._crs = crs
        self._locator = locator
        self._name = name

    def __eq__(self, other: Any) -> bool:
        """
        True if another object is a RasterMetadata object with matching metadata
        ----------
        self == other
        True if the other input is a RasterMetadata with the same shape, dtype, nodata,
        crs, transform, and bounding box. Note that NaN NoData values are interpreted as
        equal. Also note that the metadata objects do not require the same name to
        test as equal.
        ----------
        Inputs:
            other: A second input being compared to the RasterMetadata object

        Outputs:
            bool: True if the second input is a RasterMetadata object with matching
                metadata. Otherwise False
        """
        return (
            isinstance(other, RasterMetadata)
            and self.shape == other.shape
            and self.dtype == other.dtype
            and _nodata.equal(self.nodata, other.nodata)
            and self.crs == other.crs
            and self.transform == other.transform
        )

    def __repr__(self) -> str:
        """
        Returns a string summarizing the raster metadata
        ----------
        repr(self)
        str(self)
        Returns a string summarizing key information about the raster metadata.
        ----------
        Outputs:
            str: A string summary of the raster metadata
        """

        # CRS
        if self.crs is None:
            crs = "CRS: None"
        else:
            crs = f'CRS("{self.crs.name}")'

        # Transform and bounds
        if self.transform is None:
            transform = "Transform: None"
            bounds = "BoundingBox: None"
        else:
            transform = str(self.transform)
            bounds = str(self.bounds)

        # Build final string
        return (
            f"RasterMetadata:\n"
            f"    Name: {self.name}\n"
            f"    Shape: {self.shape}\n"
            f"    Dtype: {self.dtype}\n"
            f"    NoData: {self.nodata}\n"
            f"    {crs}\n"
            f"    {transform}\n"
            f"    {bounds}\n"
        )

    def __getitem__(
        self, indices: tuple[int | slice, int | slice], return_slices: bool = False
    ) -> RasterMetadata:
        """
        Returns the metadata object for the selected portion of the abstracted data array
        ----------
        self[rows, cols]
        Returns a copy of the metadata for the selected portion of the metadata's
        abstracted data array. The "rows" input should be an index or slice as would be
        applied to the first dimension of a 2D numpy array with the same shape as the
        metadata. The "cols" input is an index or slice as would be applied to the
        second dimension. Returns an object with an updated shape. Also updates the
        Transform and BoundingBox as appropriate.

        Note that this syntax has several limitations compared to numpy array indexing.
        As follows:
        1. Indexing is not supported when the metadata shape includes a 0,
        2. Indices must select at least 1 pixel - empty selections are not supported,
        3. Slices must have a step size of 1 or None,
        4. You must provide indices for exactly 2 dimensions, and
        5. This syntax is limited to the int and slice indices available to Python
        lists. More advanced numpy indexing methods (such as boolean indices and
        ellipses) are not supported.

        self.__getitem__((rows, cols), return_slices=True)
        Returns the standardized row and column slices for the new array in addition to
        the new metadata object. The two extra outputs are the slices of the data array
        corresponding to the new metadata object. Start and stop indices will always be
        positive, and the step size will always be 1.
        ----------
        Inputs:
            rows: An index or slice for the first dimension of a numpy array with the
                same shape as the metadata
            cols: An index or slice for the second dimension of a numpy array with the
                same shape as the metadata

        Outputs:
            RasterMetadata: The metadata object for the indexed portion of the
                abstracted data array
            slice (optional): The row slice corresponding to the new metadata
            slice (optional): The column slice corresponding to the new metadata
        """

        # Validate
        rows, cols = rvalidate.slices(indices, self.shape)

        # Compute new shape
        nrows = rows.stop - rows.start
        ncols = cols.stop - cols.start
        shape = (nrows, ncols)

        # Compute new transform as possible
        if self.transform is None:
            transform = None
        else:
            dx = self.dx("base")
            dy = self.dy("base")
            left = self.left + cols.start * dx
            top = self.top + rows.start * dy
            transform = Transform(dx, dy, left, top, self.crs)

        # Return updated metadata
        metadata = self.update(shape=shape, transform=transform)
        if return_slices:
            return metadata, rows, cols
        else:
            return metadata

    def todict(self) -> dict[str, Any]:
        """
        Returns a dict representation of the metadata object
        ----------
        self.todict()
        Returns a dict representing the metadata object. The dict will have the
        following keys: "shape", "dtype", "nodata", "crs", "transform", "bounds", and
        "name".
        ----------
        Outputs:
            dict: A dict representation of the metadata object
        """

        return {
            "shape": self.shape,
            "dtype": self.dtype,
            "nodata": self.nodata,
            "crs": self.crs,
            "transform": self.transform,
            "bounds": self.bounds,
            "name": self.name,
        }

    #####
    # Updated objects
    #####

    def update(
        self,
        *,
        dtype: Optional[type] = None,
        nodata: Optional[scalar] = None,
        casting: str = "safe",
        # Spatial
        crs: Optional[CRSInput] = None,
        transform: Optional[TransformInput] = None,
        bounds: Optional[BoundsInput] = None,
        # Shape and name
        shape: Optional[shape2d] = None,
        keep_bounds: bool = False,
        name: Optional[str] = None,
    ) -> RasterMetadata:
        """
        Returns a RasterMetadata object with updated fields
        ----------
        self.update(*, dtype)
        self.update(*, nodata)
        self.update(*, nodata, casting)
        Returns a new RasterMetadata object with updated data array metadata. If the
        updated object does not have a dtype and you provide a NoData value, then the
        updated object will inherit the dtype of that value. Otherwise, a new NoData
        value will be cast to the dtype of the updated raster. By default, requires
        safe casting, but see the "casting" options to use other casting rules.

        self.update(*, crs)
        self.update(*, transform)
        self.update(*, bounds)
        Returns an object with updated spatial metadata. Note that you may only provide
        one of the "transform" and "bounds" options - these two inputs are mutually
        exclusive. If the updated object has a CRS that differs from the transform/bounds, 
        then the transform/bounds will be reprojected. If the updated object does not 
        have a crs, then it will inherit any CRS from the transform/bounds.

        self.update(*, shape)
        self.update(*, shape, keep_bounds=True)
        Returns a new RasterMetadata object with a different shape. If you do not also
        update the transform or bounds, then the method will need to compute a new
        Transform or BoundingBox. By default, keeps the original transform and computes
        a new BoundingBox for the shape. Set keep_bounds=True to instead keep the
        original BoundingBox and compute a new Transform. Note that this option is
        ignored if you provide a new transform or bounds.

        self.update(*, name)
        Returns an object with an updated name.
        ----------
        Inputs:
            dtype: A new data dtype
            nodata: A new NoData value
            casting: The casting rule when casting a NoData value to the dtype. Options
                are "safe" (default), "same_kind", "no", "equiv", and "unsafe"
            crs: A new coordinate reference system
            transform: A new affine transform
            bounds: A new bounding box
            shape: A new data array shape
            keep_bounds: True to keep the original BoundingBox when the shape is
                updated. False (default) to keep the original transform. Ignored if a
                new transform or bounds is provided
            name: A new identifying name

        Outputs:
            RasterMetadata: A new RasterMetadata object with updated metadata fields.
        """

        # Initialize basic fields. Use current value if no update is provided
        kwargs = {
            "shape": shape,
            "dtype": dtype,
            "nodata": nodata,
            "crs": crs,
            "name": name,
        }
        for name, value in kwargs.items():
            if value is None:
                kwargs[name] = getattr(self, name)
        kwargs["casting"] = casting

        # Inherit the original transform or bounds if no update is provided
        if all_nones(transform, bounds):
            if keep_bounds:
                kwargs["bounds"] = self.bounds
            else:
                kwargs["transform"] = self.transform

        # Otherwise, use the new values
        else:
            kwargs["transform"] = transform
            kwargs["bounds"] = bounds

        # Return updated object
        return RasterMetadata(**kwargs)

    def copy(self) -> RasterMetadata:
        """
        Returns a copy of the current metadata object
        ----------
        self.copy()
        Returns a copy of the metadata object.
        ----------
        Outputs:
            RasterMetadata: A copy of the current RasterMetadata object
        """
        return self.update()

    def _create(
        self,
        isbool: bool,
        ensure_nodata: bool,
        default_nodata: Optional[Any] = None,
        casting: Optional[Any] = None,
    ) -> RasterMetadata:
        """Updates metadata for isbool and ensure_nodata factory options. The name
        _create is by analogy with the Raster._create function, as this command
        implements the metadata manipulations of that function."""

        if isbool:
            return self.as_bool()
        elif ensure_nodata:
            return self.ensure_nodata(default_nodata, casting)
        else:
            return self

    def as_bool(self):
        """
        Sets dtype to bool and NoData to False
        ----------
        self.as_bool()
        Returns a copy of the current object suitable for a boolean data array. The
        dtype of the new object is set to bool, and the NoData value is set to False.
        ----------
        Outputs:
            RasterMetadata: A copy of the current object with dtype=bool and nodata=False
        """

        return self.update(dtype=bool, nodata=False)

    def ensure_nodata(
        self, default: Optional[scalar] = None, casting: str = "safe"
    ) -> RasterMetadata:
        """
        Returns a RasterMetadata object guaranteed to have a NoData value
        ----------
        self.ensure_nodata()
        Checks if the current object has a metadata object. If so, returns a copy of the
        current object. If not, returns a metadata object with a default NoData value
        for the dtype. Raises a ValueError if the object has neither a NoData value nor
        a dtype.

        self.ensure_nodata(default)
        self.ensure_nodata(default, casting)
        Specifies the default NoData value to use if the metadata does not already have
        a NoData value. If the metadata object does not have a dtype, then the new
        object will also inherit the dtype of the NoData value. Otherwise, the NoData
        value is cast to the metadata's dtype. By default, requires safe casting, but
        see the "casting" option to select other casting rules.
        ----------
        Inputs:
            default: The NoData value to use if the metadata does not already have
                a NoData value
            casting: The casting rule used to convert "default" to the metadata dtype.
                Options are "safe" (default), "same_kind", "equiv", "no", and "unsafe"

        Outputs:
            RasterMetadata: A new RasterMetadata object guaranteed to have a NoData value
        """

        # No change if there's already a NoData value
        if self.nodata is not None:
            return self.copy()

        # Require a dtype if the user did not provide a default value
        if all_nones(self.dtype, default):
            raise ValueError(
                f"Cannot ensure nodata because the {self.name} metadata "
                "does not have a dtype"
            )

        # Parse NoData and dtype. Return the updated object
        elif default is None and self.dtype is not None:
            nodata = default_nodata(self.dtype)
        else:
            nodata = default
        return self.update(nodata=nodata, casting=casting)

    #####
    # Factories
    #####

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
    ) -> RasterMetadata:
        """
        Returns the RasterMetadata object for a file-based raster
        ----------
        RasterMetadata.from_file(path)
        RasterMetadata.from_file(path, name)
        Returns the RasterMetadata object for the raster in the indicated file. Raises
        a FileNotFoundError if the file cannot be located. By default, records the dtype
        of band 1, but see below for additional options. The "name" input can be used to
        provide an optional name for the metadata, defaults to "raster" if unset. By
        default, if the file does not have a NoData value, then selects a default value
        based on the dtype. See below for other NoData options.

        Also, by default the method will attempt to use the file extension to
        detect the file format driver used to read data from the file. Raises an
        Exception if the driver cannot be determined, but see below for options
        to explicitly set the driver. You can also use:
            >>> pfdf.utils.driver.extensions('raster')
        to return a summary of supported file format drivers, and their associated
        extensions.

        Raster.from_file(..., *, bounds)
        Returns the RasterMetadata object for a bounded subset of the saved dataset.
        The "bounds" input indicates a rectangular portion of the saved dataset
        whose metadata should be determined. If the window extends beyond the bounds of
        the dataset, then the dataset will be windowed to the relevant bound, but no
        further. The window may be a BoundingBox, Raster, RasterMetadata, or a
        list/tuple/dict convertible to a BoundingBox object.

        Raster.from_file(..., *, band)
        Specify the raster band to use to determine the dtype. Raster bands use
        1-indexing (and not the 0-indexing common to Python). Raises an error if the
        band does not exist.

        Raster.from_file(..., *, isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the file data values. The output metadata object will have a bool
        dtype, and its NoData value will be set to False.

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
            name: An optional name for the metadata. Defaults to "raster"
            bounds: A BoundingBox-like object indicating a subset of the saved raster
                whose metadata should be determined
            band: The raster band from which to read the dtype. Uses 1-indexing and
                defaults to 1
            isbool: True to set dtype to bool and NoData to False. If False (default),
                preserves the original dtype and NoData.
            ensure_nodata: True (default) to assign a default NoData value based
                on the raster dtype if the file does not record a NoData value.
                False to leave missing NoData as None.
            default_nodata: The default NoData value to use if the raster file is
                missing one. Overrides any default determined from the raster's dtype.
            casting: The casting rule to use when converting the default NoData
                value to the raster's dtype.
            driver: A file format to use to read the raster, regardless of extension

        Outputs:
            RasterMetadata: The metadata object for the raster
        """

        # Validate inputs. Open file and get full-file metadata
        path, bounds = rvalidate.file(path, driver, band, bounds, casting)
        with rasterio.open(path) as file:
            metadata = factory.file(file, band, name)

        # Update metadata for windowed reading, isbool, and/or ensure_nodata
        if bounds is not None:
            metadata, _ = factory.window(metadata, bounds)
        return metadata._create(isbool, ensure_nodata, default_nodata, casting)

    @staticmethod
    def from_rasterio(
        reader: rasterio.DatasetReader,
        name: Optional[str] = None,
        *,
        band: int = 1,
        isbool: bool = False,
        bounds: Optional[BoundsInput] = None,
        ensure_nodata: bool = True,
        default_nodata: Optional[scalar] = None,
        casting: str = "safe",
    ) -> RasterMetadata:
        """
        Builds a new RasterMetadata object from a rasterio.DatasetReader
        ----------
        RasterMetadata.from_rasterio(reader)
        RasterMetadata.from_rasterio(reader, name)
        Creates a new RasterMetadata object from a rasterio.DatasetReader. Raises a
        FileNotFoundError if the associated file no longer exists. Uses the file
        format driver associated with the object to read the raster from file.
        By default, records the dtype for band 1. The "name" input specifies an optional
        name for the new metadata. Defaults to "raster" if unset.

        RasterMetadata.from_rasterio(..., *, bounds)
        Returns the RasterMetadata object for a bounded subset of the saved dataset.
        The "bounds" input indicates a rectangular portion of the saved dataset
        whose metadata should be determined. If the window extends beyond the bounds of
        the dataset, then the dataset will be windowed to the relevant bound, but no
        further. The window may be a BoundingBox, Raster, RasterMetadata, or a
        list/tuple/dict convertible to a BoundingBox object.

        RasterMetadata.from_rasterio(..., band)
        Specify the raster band to use to determine the dtype. Raster bands use
        1-indexing (and not the 0-indexing common to Python). Raises an error if the
        band does not exist.

        RasterMetadata.from_rasterio(..., *, isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the file data values. The output metadata object will have a bool
        dtype, and its NoData value will be set to False.

        RasterMetadata.from_rasterio(..., *, default_nodata)
        RasterMetadata.from_rasterio(..., *, default_nodata, casting)
        RasterMetadata.from_rasterio(..., *, ensure_nodata=False)
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
            name: An optional name for the metadata. Defaults to "raster"
            bounds: A BoundingBox-like object indicating a subset of the saved raster
                whose metadata should be determined
            band: The raster band from which to read the dtype. Uses 1-indexing and
                defaults to 1
            isbool: True to set dtype to bool and NoData to False. If False (default),
                preserves the original dtype and NoData.
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

        path = rvalidate.reader(reader)
        return RasterMetadata.from_file(
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

    @staticmethod
    def from_pysheds(
        sraster: PyshedsRaster, name: Optional[str] = None, isbool: bool = False
    ) -> RasterMetadata:
        """
        Creates a RasterMetadata from a pysheds.sview.Raster object
        ----------
        RasterMetadata.from_pysheds(sraster)
        RasterMetadata.from_pysheds(sraster, name)
        Creates a new RasterMetadata object from a pysheds.sview.Raster object. Inherits
        the nodata values, CRS, and transform of the pysheds Raster. The "name" input
        specifies an optional name for the metadata. Defaults to "raster" if
        unset.

        RasterMetadata.from_pysheds(..., *, isbool=True)
        Indicates that the raster represents a boolean array, regardless of the
        dtype of the file data values. The metadata object will have a bool dtype, and
        its NoData value will be set to False.
        ----------
        Inputs:
            sraster: The pysheds.sview.Raster object used to create the RasterMetadata
            name: An optional name for the metadata. Defaults to "raster"
            isbool: True to set dtype to bool and NoData to False. If False (default),
                preserves the original dtype and NoData.

        Outputs:
            RasterMetadata: The new metadata object
        """

        metadata = factory.pysheds(sraster, name)
        return metadata._create(isbool, ensure_nodata=False)

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
        spatial: Optional[RasterMetadata] = None,
        isbool: bool = False,
        ensure_nodata: bool = True,
    ) -> RasterMetadata:
        """
        Create a RasterMetadata object from a numpy array
        ----------
        RasterMetadata.from_array(array, name)
        Creates a RasterMetadata object from a numpy array. Infers a NoData value
        from the dtype of the array. The Transform and CRS will both be None. The "name"
        input specifies an optional name for the metadata. Defaults to "raster" if unset.

        RasterMetadata.from_array(..., *, nodata)
        RasterMetadata.from_array(..., *, nodata, casting)
        Specifies a NoData value for the metadata. The NoData value will be cast to
        the same dtype as the array. Raises a TypeError if the NoData value cannot
        be safely cast to this dtype. Use the casting option to change this behavior.
        Casting options are as follows:
        'no': The data type should not be cast at all
        'equiv': Only byte-order changes are allowed
        'safe': Only casts which can preserve values are allowed
        'same_kind': Only safe casts or casts within a kind (like float64 to float32)
        'unsafe': Any data conversions may be done

        RasterMetadata.from_array(..., *, spatial)
        Specifies a Raster or RasterMetadata object to use as a default spatial metadata
        template. By default, transform and crs properties from the template will be
        copied to the new raster. However, see below for a syntax to override this behavior.

        RasterMetadata.from_array(..., *, crs)
        RasterMetadata.from_array(..., *, transform)
        RasterMetadata.from_array(..., *, bounds)
        Specifies the crs, transform, and/or bounding box for the metadata. If used in
        conjunction with the "spatial" option, then any keyword options will take
        precedence over the metadata in the spatial template. You may only provide one
        of the transform/bounds inputs - raises an error if both are provided. If the
        CRS of a Transform or BoundingBox differs from the template/keyword CRS, then
        the Transform or BoundingBox is reprojected to match the other CRS.

        RasterMetadata.from_array(..., *, isbool=True)
        Indicates that the metadata represents a boolean array, regardless of the
        dtype of the array. The newly created metadata will have a bool dtype and
        values, and its NoData value will be set to False.

        RasterMetadata.from_array(..., *, ensure_nodata=False)
        Disables the use of default NoData values. The new metadata's nodata
        value will be None unless the "nodata" option is specified.
        ----------
        Inputs:
            array: A 2D numpy array whose data values represent a raster
            name: An optional name for the metadata. Defaults to "raster"
            nodata: A NoData value for the raster metadata
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
            spatial: A Raster or RasterMetadata object to use as a default spatial
                metadata template
            crs: A coordinate reference system
            transform: An affine transformation for the raster. Mutually exclusive
                with the "bounds" input
            bounds: A BoundingBox for the raster. Mutually exclusive with the
                "transform" input
            isbool: True to set dtype to bool and NoData to False. If False (default),
                preserves the original dtype and NoData.
            ensure_nodata: True (default) to infer a default NoData value from the
                array's dtype when a NoData value is not provided. False to
                disable this behavior.

        Outputs:
            Raster: A raster object for the array-based raster dataset
        """

        metadata, _ = factory.array(
            array, name, nodata, casting, crs, transform, bounds, spatial, copy=False
        )
        return metadata._create(isbool, ensure_nodata, nodata, casting)

    #####
    # Vector features
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
        # Spatial options
        bounds: Optional[BoundsInput] = None,
        resolution: ResolutionInput = 10,
        units: Units = "meters",
        # File IO
        layer: Optional[int | str] = None,
        driver: Optional[str] = None,
        encoding: Optional[str] = None,
    ) -> RasterMetadata:
        """
        Creates a RasterMetadata from a set of point/multi-point features
        ----------
        RasterMetadata.from_points(path)
        Returns metadata derived from the input point features. The contents of
        the input file should resolve to a FeatureCollection of Point and/or
        MultiPoint geometries (and see below if the file contains multiple layers).
        The CRS of the output metadata is inherited from the input feature file.
        The default resolution of the output metadata is 10 meters, although see
        below to specify other resolutions. The bounds of the metadata will be the
        minimal bounds required to contain all input points at the indicated
        resolution.

        If you do not specify an attribute field, then the metadata will
        have a boolean dtype. See below to build the metadata from an data property
        field instead.

        By default, this method will attempt to guess the intended file format and
        encoding based on the path extension. Raises an error if the format or
        encoding cannot be determined. However, see below for syntax to specify
        the driver and encoding, regardless of extension. You can also use:
            >>> pfdf.utils.driver.extensions('vector')
        to return a summary of supported file format drivers, and their associated
        extensions.

        RasterMetadata.from_points(path, field)
        RasterMetadata.from_points(..., *, dtype)
        RasterMetadata.from_points(..., *, dtype, field_casting)
        Builds the metadata using one of the data property fields for the point features.
        The indicated data field must exist in the data properties, and must have an int
        or float type. By default, the dtype of the output raster will be int32 or
        float64, as appropriate for the data field type. Use the "dtype" option to
        specify a different dtype instead. In this case, the data field values will be
        cast to the indicated dtype before being used to build the metadata. By default, 
        field values must be safely castable to the indicated dtype. Use the
        "field_casting" option to select different casting rules. The "dtype" and
        "field_casting" options are ignored if you do not specify a field.

        RasterMetadata.from_points(..., field, *, nodata)
        RasterMetadata.from_points(..., field, *, nodata, casting)
        Specifies the NoData value to use when building the metadata from a data attribute
        field. By default, the NoData value must be safely castable to the dtype of the
        output raster. Use the "casting" option to select other casting rules. NoData
        options are ignored if you do not specify a field.

        Raster.from_points(..., field, *, operation)
        Applies the indicated function to the data field values. The input function
        should accept one numeric input, and return one real-valued numeric output.
        Useful when data field values require a conversion. For example, you could use
        the following to scale Point values by a factor of 100:

            def times_100(value):
                return value * 100

            RasterMetadata.from_points(..., field, operation=times_100)

        Values are converted before they are validated against the "dtype" and
        "field_casting" options, so you can also use an operation to implement a custom
        conversion from data values to the output raster dtype. The operation input is
        ignored if you do not specify a field.

        RasterMetadata.from_points(..., *, bounds)
        Only uses point features contained within the indicated bounds. The returned
        metadata is also clipped to these bounds. This option can be useful when
        you only need data from a subset of a much larger Point dataset.

        RasterMetadata.from_points(path, *, resolution)
        RasterMetadata.from_points(path, *, resolution, units)
        Specifies the resolution of the output raster. The resolution may be a
        scalar positive number, a 2-tuple of such numbers, a Transform, a Raster, or a
        RasterMetadata object. If a scalar, indicates the resolution of the output raster
        for both the X and Y axes. If a 2-tuple, the first element is the X-axis resolution
        and the second element is the Y-axis. If a Raster/RasterMetadata/Transform, uses
        the associated resolution. Raises an error if a Raster/RasterMetadata does not
        have a Transform.

        If the resolution input does not have an associated CRS, then the resolution
        values are interpreted as meters. Use the "units" option to interpret
        resolution values in different units instead. Supported units include:
        "base" (CRS/Transform base unit), "kilometers", "feet", and "miles".
        Note that this option is ignored if the input resolution has a CRS.

        RasterMetadata.from_points(..., *, layer)
        Use this option when the input feature file contains multiple layers. The
        "layer" input indicates the layer holding the relevant Point geometries.
        This may be either an integer index, or the (string) name of a layer in
        the input file.

        RasterMetadata.from_points(..., *, driver)
        RasterMetadata.from_points(..., *, encoding)
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
            dtype: The dtype of the output metadata when building from a data field
            field_casting: The type of data casting allowed to occur when converting
                data field values to a specified output dtype. Options are "no",
                "equiv", "safe" (default), "same_kind", and "unsafe".
            nodata: The NoData value for the metadataa
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
            operation: A function that should be applied to data field values before
                they are used to build the metadata. Should accept one numeric input and
                return one real-valued numeric input.
            bounds: A bounding box indicating the subset of point features that
                should be used to create the metadata.
            resolution: The desired resolution of the output metadata
            units: Specifies the units of the resolution when the resolution input
                does not have a CRS. Options include: "base" (CRS/Transform base
                unit), "meters" (default), "kilometers", "feet", and "miles"
            layer: The layer of the input file from which to load the point geometries
            driver: The file-format driver to use to read the Point feature file
            encoding: The encoding of the Point feature file

        Outputs:
            RasterMetadata: The point-derived metadata
        """

        _, metadata = factory.points(
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
        return metadata

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
    ) -> RasterMetadata:
        """
        Creates RasterMetadata from a set of polygon/multi-polygon features
        ----------
        RasterMetadata.from_polygons(path)
        Returns metadata derived from the input polygon features. The contents of
        the input file should resolve to a FeatureCollection of Polygon and/or
        MultiPolygon geometries (and see below if the file contains multiple layers).
        The CRS of the metadata is inherited from the input feature file.
        The default resolution of the metadata is 10 meters, although see
        below to specify other resolutions. The bounds will be the
        minimal bounds required to contain all input polygons at the indicated
        resolution.

        If you do not specify an attribute field, then the returned metadata will
        have a boolean dtype. See below to build the raster from an data property field
        instead.

        By default, this method will attempt to guess the intended file format and
        encoding based on the path extension. Raises an error if the format or
        encoding cannot be determined. However, see below for syntax to specify
        the driver and encoding, regardless of extension. You can also use:
            >>> pfdf.utils.driver.extensions('vector')
        to return a summary of supported file format drivers, and their associated
        extensions.

        RasterMetadata.from_polygons(path, field)
        RasterMetadata.from_polygons(..., *, dtype)
        RasterMetadata.from_polygons(..., *, dtype, field_casting)
        Builds the metadata using one of the data property fields for the polygon
        features. The indicated data field must exist in the data properties, and must
        have an int or float type. By default, the dtype of the metadata will be
        int32 or float64, as appropriate. Use the "dtype" option to specify the metadata
        dtype instead. In this case, the data field values will be cast to the indicated
        dtype before being used to build the metadata. Note that only some numpy dtypes
        are supported for building metadata from polygons. Supported dtypes are: bool,
        int16, int32, uint8, uint16, uint32, float32, and float64. Raises an error if
        you select a different dtype.

        By default, field values must be safely castable to the indicated dtype. Use the
        "field_casting" option to select different casting rules. The "dtype" and
        "field_casting" options are ignored if you do not specify a field.

        RasterMetadata.from_polygons(..., field, *, nodata)
        RasterMetadata.from_polygons(..., field, *, nodata, casting)
        Specifies the NoData value to use when building the metadata from a data attribute
        field. By default, the NoData value must be safely castable to the dtype of the
        output raster. Use the "casting" option to select other casting rules. NoData
        options are ignored if you do not specify a field.

        RasterMetadata.from_polygons(..., field, *, operation)
        Applies the indicated function to the data field values and uses the output
        values to build the metadata. The input function should accept one numeric input,
        and return one real-valued numeric output. Useful when data field values require
        a conversion. For example, you could use the following to scale Polygon values
        by a factor of 100:

            def times_100(value):
                return value * 100

            RasterMetadata.from_polygons(..., field, operation=times_100)

        Values are converted before they are validated against the "dtype" and
        "field_casting" options, so you can also use an operation to implement a custom
        conversion from data values to the output raster dtype. The operation input is
        ignored if you do not specify a field.

        RasterMetadata.from_polygons(..., *, bounds)
        Only uses polygon features that intersect the indicated bounds. The
        returned metadata is also clipped to these bounds. This option can be useful
        when you only need data from a subset of a much larger Polygon dataset.

        RasterMetadata.from_polygons(..., *, resolution)
        RasterMetadata.from_polygons(..., *, resolution, units)
        Specifies the resolution of the metadata. The resolution may be a
        scalar positive number, a 2-tuple of such numbers, a Transform, a Raster, or a
        RasterMetadata object. If a scalar, indicates the resolution of the output raster for both
        the X and Y axes. If a 2-tuple, the first element is the X-axis resolution
        and the second element is the Y-axis. If a Raster/RasterMetadata/Transform, uses
        the associated resolution. Raises an error if a Raster/RasterMetadata does not
        have a Transform.

        If the resolution input does not have an associated CRS, then the resolution
        values are interpreted as meters. Use the "units" option to interpret
        resolution values in different units instead. Supported units include:
        "base" (CRS/Transform base unit), "kilometers", "feet", and "miles".
        Note that this option is ignored if the input resolution has a CRS.

        RasterMetadata.from_polygons(..., *, layer)
        Use this option when the input feature file contains multiple layers. The
        "layer" input indicates the layer holding the relevant Polygon geometries.
        This may be either an integer index, or the (string) name of a layer in
        the input file.

        RasterMetadata.from_polygons(..., *, driver)
        RasterMetadata.from_polygons(..., *, encoding)
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
            dtype: The dtype of the metadata when building from a data field
            field_casting: The type of data casting allowed to occur when converting
                data field values to a specified output dtype. Options are "no",
                "equiv", "safe" (default), "same_kind", and "unsafe".
            nodata: The NoData value for the metadata
            casting: The type of data casting allowed to occur when converting a
                NoData value to the dtype of the raster. Options are "no", "equiv",
                "safe" (default), "same_kind", and "unsafe".
            operation: A function that should be applied to data field values before
                they are used to build the raster. Should accept one numeric input and
                return one real-valued numeric input.
            bounds: A bounding box indicating the subset of polygon features that
                should be used to create the raster.
            resolution: The desired resolution of the metadata
            units: Specifies the units of the resolution when the resolution input
                does not have a CRS. Options include: "base" (CRS/Transform base
                unit), "meters" (default), "kilometers", "feet", and "miles"
            layer: The layer of the input file from which to load the polygon geometries
            driver: The file-format driver to use to read the Polygon feature file
            encoding: The encoding of the Polygon feature file

        Outputs:
            RasterMetadata: The polygon-derived metadata
        """

        _, metadata = factory.polygons(
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
        return metadata

    #####
    # Preprocessing
    #####

    def fill(self) -> RasterMetadata:
        """
        Returns a metadata object without a NoData value
        ----------
        self.fill()
        Returns a copy of the current RasterMetadata that does not have a NoData value.
        ----------
        Outputs:
            RasterMetadata: A metadata object without a NoData value
        """

        metadata = self.copy()
        metadata._nodata = None
        return metadata

    def buffer(
        self,
        distance: Optional[scalar] = None,
        units: BufferUnits = "meters",
        *,
        left: Optional[scalar] = None,
        bottom: Optional[scalar] = None,
        right: Optional[scalar] = None,
        top: Optional[scalar] = None,
        return_buffers: bool = False,
    ) -> RasterMetadata | tuple[RasterMetadata, EdgeDict]:
        """
        Returns the metadata object for a buffered raster
        ----------
        self.buffer(distance, units)
        Returns a new RasterMetadata object for the raster that would occur if the
        current metadata object's raster were buffered by the specified distance. The
        input distance must be positive and is interpreted as meters by default. Use
        the "units" option to provide the buffering distance in different units instead.
        Supported units include: "pixels" (the number of pixels to buffer along each
        edge), "base" (CRS/Transform base units), "meters", "kilometers", "feet", and
        "miles".

        Note that all units excepts "base" and "pixels" require the metadata object to
        have a CRS. Additionally, all units except "pixels" require the metadata object
        to have a transform.

        self.buffer(*, left)
        self.buffer(*, right)
        self.buffer(*, bottom)
        self.buffer(*, top)
        Specify the buffering distance for a particular direction. The "distance" input
        is optional (but still permitted) if any of these options are specified. If
        both the "distance" input and one of these options are specified, then
        the direction-specific option takes priority. If a direction does not
        have a distance and the "distance" input is not provided, then no buffering
        is applied to that direction.

        self.buffer(*, return_buffers=True)
        Returns the pixel_buffers dict in addition to the new metadata object. The
        new metadata object will be the first output, and the pixel dict will be the
        second output. The pixel_buffers dict contains the following keys: "left",
        "bottom", "right", and "top". The value for each key is the number of buffering
        pixels that would be applied to each side of the data array.
        ----------
        Inputs:
            distance: A default buffer for all sides
            units: Specifies the units of the input buffers. Options include:
                "pixels", "base", "meters" (default), "kilometers", "feet", and "miles"
            left: A buffer for the left side of the raster
            right: A buffer for the right side of the raster
            top: A buffer for the top of the raster
            bottom: A buffer for the bottom of the raster
            return_buffers: True to also return a pixel buffers dict. False (default) to
                only return the updated metadata

        Outputs:
            RasterMetadata: The metadata object for the buffered raster
            dict[str, float] (Optional): A dict with the following keys: "left", "bottom",
                "right", and "top". The value for each key is the number of buffering
                pixels that  would be applied to each side of the data array. Only
                returned if return_buffers=True
        """

        # Validate buffers and units
        units = cvalidate.units(units, include="pixels")
        if units != "pixels" and self.transform is None:
            raise MissingTransformError(
                f"Cannot buffer {self.name} because it does not have an affine "
                "transform. Note that a transform is not required when buffering with "
                'the units="pixels" option.'
            )
        elif units not in ["base", "pixels"] and self.crs is None:
            raise MissingCRSError(
                f"Cannot convert buffering distances from {units} because {self.name} "
                "does not have a CRS. Note that a CRS is not required when buffering "
                'with the units="base" or units="pixels" options.'
            )
        buffers = cvalidate.buffers(distance, left, bottom, right, top)

        # Build conversion dict from axis units to pixels
        if units != "pixels":
            xres, yres = self.resolution("base")
            resolution = {"left": xres, "right": xres, "top": yres, "bottom": yres}

        # Convert buffers to a whole number of pixels
        if units not in ["base", "pixels"]:
            buffers = _buffers.buffers_to_base(self, buffers, units)
        for name, buffer in buffers.items():
            if units != "pixels":
                buffer = buffer / resolution[name]
            buffers[name] = ceil(buffer)

        # Compute the new shape
        nrows = self.nrows + buffers["top"] + buffers["bottom"]
        ncols = self.ncols + buffers["left"] + buffers["right"]
        shape = nrows, ncols

        # Compute the new transform
        if self.transform is None:
            transform = None
        else:
            dx = self.dx("base")
            dy = self.dy("base")
            left = self.left - dx * buffers["left"]
            top = self.top - dy * buffers["top"]
            transform = Transform(dx, dy, left, top)

        # Return updated object and optionally buffers
        metadata = self.update(shape=shape, transform=transform)
        if return_buffers:
            return metadata, buffers
        else:
            return metadata

    def clip(self, bounds: BoundsInput, return_limits: bool = False) -> RasterMetadata:
        """
        Returns the RasterMetadata object for a clipped raster
        ----------
        self.clip(bounds)
        Returns the RasterMetadata object for the raster that would occur if the current
        metadata object's raster were clipped to the indicated bounds. The bounds may be
        a Raster, RasterMetadata, BoundingBox, dict, list, or tuple representing a
        bounding box. Note that the output metadata will inherit the bounding box CRS
        if the current metadata object does not already have a CRS.

        self.clip(..., return_limits = True)
        Also return the pixel index limits for the clipping operation. The limits
        indicate the first and last indices of the clipped array, relative to the current
        array. Limits will be negative or larger than the current array shape if the
        metadata is clipped outside its current bounds. Returns the new metadata object
        as the first output, the row index limits, and then the column index limits.
        ----------
        Inputs:
            bounds: The bounds of the clipped raster
            return_limits: True to also return pixel index limits. False (default) to
                only return the updated array

        Outputs:
            RasterMetadata: The RasterMetadata object for the raster that would occur
                if the current metadata's raster were clipped to the bounds
            (int, int) (Optional): The index limits of the clipped array's rows. Only
                returned if return_limits=True
            (int, int) (Optional): The index limits of the clipped array's columns. Only
                returned if return_limits=True
        """

        # Require a transform
        if self.transform is None:
            raise MissingTransformError(
                f"Cannot clip {self.name} because it does not have an affine Transform."
            )

        # Parse bounds and CRS
        bounds = pvalidate.bounds(bounds)
        bounds = bounds.match_crs(self.crs)
        bounds = bounds.orient(self.orientation)

        # Get index limits. Order from min to max
        rows, cols = rowcol(self.affine, bounds.xs, bounds.ys, op=round)
        rows = (min(rows), max(rows))
        cols = (min(cols), max(cols))

        # Compute new shape and transform
        shape = (rows[1] - rows[0], cols[1] - cols[0])
        transform = Transform(
            self.dx("base"), self.dy("base"), bounds.left, bounds.top, bounds.crs
        )

        # Return updated metadata and optionally index limits
        metadata = self.update(shape=shape, transform=transform)
        if return_limits:
            return metadata, rows, cols
        else:
            return metadata

    def reproject(
        self,
        template: Optional[Template] = None,
        *,
        crs: Optional[CRSInput] = None,
        transform: Optional[TransformInput] = None,
    ) -> RasterMetadata:
        """
        Returns the RasterMetadata object for a reprojected raster
        ----------
        self.reproject(template)
        Returns the RasterMetadata object for the raster that would occur if the current
        metadata object's raster were reprojected to match a template raster. The new
        metadata object will have the same CRS, resolution, and grid alignment as the
        template. The template may be a Raster or RasterMetadata object.

        self.reproject(..., *, crs)
        self.reproject(..., *, transform)
        Specify the CRS and/or transform of the reprojected raster. If you provide one
        of these keyword options in addition to a template, then the keyword value will
        take priority.
        ----------
        Inputs:
            template: A Raster or RasterMetadata object that defines the CRS, resolution
                and grid alignment of the reprojected raster
            crs: The CRS for the reprojection. Overrides the template CRS
            transform: The transform used to determine resolution and grid alignment.
                Overrides the template transform
        """

        # Validate. Require a reprojection parameter and transform
        if all_nones(template, crs, transform):
            raise ValueError(
                "The template, crs, and transform inputs cannot all be None."
            )
        elif self.transform is None:
            raise MissingTransformError(
                f"Cannot reproject {self.name} because it does not have an "
                "affine Transform."
            )

        # Validate metadata. Parse CRS and transform
        kwargs = RasterMetadata(self.shape, crs=crs, transform=transform)
        template = parse.template(kwargs, template, "template raster")
        if template.transform is None:
            template = template.update(transform=self.transform)
        if template.crs is None:
            template = template.update(crs=self.crs)

        # Compute reprojected transform and shape. Update metadata
        transform, shape = align.reprojection(self.bounds, template)
        return self.update(shape=shape, crs=template.crs, transform=transform)

    #####
    # Testing
    #####

    def isclose(self, other: Any, rtol: scalar = 1e-5, atol: scalar = 1e-8) -> bool:
        """
        True if two RasterMetadata objects are similar
        ----------
        self.isclose(other)
        Tests if another RasterMetadata object has similar values to the current object.
        Tests the shape, dtype, nodata, crs, and transform. To test as True, the two
        objects must meet the following conditions:
            * shape, dtype, and nodata must be equal,
            * CRSs are compatible, and
            * Transform objects are similar
        To have compatible CRSs, the objects must have the same CRS or at least one CRS
        must be None. The Transform objects are tested by using numpy.allclose to
        compare dx, dy, left, and top values. The transforms are considered similar if
        numpy.allclose passes.

        self.isclose(..., rtol, atol)
        Specify the relative and absolute tolerance for the numpy.allclose check. By
        default, uses a relative tolerance of 1E-5, and an absolute tolerance of 1E-8.
        ----------
        Inputs:
            other: Another RasterMetadata object
            rtol: The relative tolerance for transform field comparison. Defaults to 1E-5
            atol: The absolute tolerance for transform field comparison. Defaults to 1E-8

        Outputs:
            bool: True if the other object is similar to the current object
        """

        # Validate. Determine if transform is similar
        cvalidate.type(other, "other", RasterMetadata, "RasterMetadata object")
        if no_nones(self.transform, other.transform):
            similar_transform = self.transform.isclose(other.transform, rtol, atol)
        else:
            similar_transform = self.transform == other.transform

        # Apply tests
        return (
            similar_transform
            and self.shape == other.shape
            and self.dtype == other.dtype
            and _nodata.equal(self.nodata, other.nodata)
            and _crs.compatible(self.crs, other.crs)
        )

    #####
    # Shape
    #####

    @property
    def shape(self) -> tuple[int, int]:
        "Returns the array shape"
        return self._shape

    @property
    def nrows(self) -> int:
        "Returns the number of array rows"
        return self.shape[0]

    @property
    def height(self) -> int:
        "Returns the number of array rows"
        return self.nrows

    @property
    def ncols(self) -> int:
        "Returns the number of array columns"
        return self.shape[1]

    @property
    def width(self) -> int:
        "Returns the number of array columns"
        return self.ncols

    @property
    def size(self) -> int:
        "Returns the number of array elements"
        return self.nrows * self.ncols

    #####
    # Data array
    #####

    @property
    def dtype(self) -> np.dtype | None:
        "Returns the array dtype"
        return self._dtype

    @property
    def nodata(self) -> ScalarArray | None:
        "Returns the NoData value"
        return self._nodata

    @property
    def name(self) -> str | None:
        "Returns the identifying name"
        return self._name

    #####
    # CRS
    #####

    @property
    def crs(self) -> CRS | None:
        "Returns the coordinate reference system"
        return self._crs

    @property
    def crs_units(self) -> tuple[str, str] | tuple[None, None]:
        "Returns the units along the CRS's X and Y axes"
        return _crs.units(self.crs)

    @property
    def crs_units_per_m(self) -> tuple[float, float] | tuple[None, None]:
        "Returns the number of CRS units per meter along the CRS's X and Y axes"
        x, y = _crs.units_per_m(self.crs, self.center_y)
        if x is not None:
            x = float(x[0])
            y = float(y[0])
        return x, y

    @property
    def utm_zone(self) -> CRS | None:
        "Returns the UTM zone CRS that contains the raster's center point"
        if self.crs is None or self.bounds is None:
            return None
        else:
            return self.bounds.utm_zone()

    #####
    # Transform
    #####

    def _get_locator(
        self, locator: BoundingBox | Transform | None
    ) -> BoundingBox | Transform | None:
        "Gets the final BoundingBox or Transform"

        # Return None if no locator
        if locator is None:
            return None

        # Otherwise, restore CRS
        else:
            class_type = type(locator)
            locator = locator.todict()
            locator["crs"] = self.crs
            return class_type.from_dict(locator)

    @property
    def transform(self) -> Transform:
        "Returns the affine Transform"

        transform = self._locator
        if isinstance(transform, BoundingBox):
            transform = transform.transform(*self.shape)
        return self._get_locator(transform)

    def _pixel(self, method: str, units: str, needs_y: bool = True) -> Any | None:
        "Returns a pixel geometry property"

        # None if there isn't a transform
        if self.transform is None:
            return None

        # Informative error if conversion to meters is not possible
        units = cvalidate.units(units)
        if self.crs is None and units != "base":
            raise MissingCRSError(
                f"Cannot convert {self.name} {method} to {units} because the raster does "
                f'not have a CRS. Set units="base" to return {method} in the '
                f"base units of the affine Transform instead."
            )

        # Return the property
        kwargs = {"units": units}
        if needs_y:
            kwargs["y"] = self.center_y
        return getattr(self.transform, method)(**kwargs)

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
                base units), "meters" (default), "kilometers", "feet", and "miles"

        Outputs:
            float: The change in X coordinate when moving one pixel right
        """
        return self._pixel("dx", units)

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
                base units), "meters" (default), "kilometers", "feet", and "miles"

        Outputs:
            float: The change in Y coordinate when moving one pixel down
        """
        return self._pixel("dy", units, needs_y=False)

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
                "feet", and "miles"

        Outputs:
            float, float: The X and Y axis pixel resolution
        """
        return self._pixel("resolution", units)

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
                "feet", and "miles"

        Outputs:
            float: The area of a raster pixel
        """
        return self._pixel("pixel_area", units)

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
                "kilometers", "feet", and "miles"

        Outputs:
            float: The area of a raster pixel
        """
        return self._pixel("pixel_diagonal", units)

    @property
    def affine(self) -> Affine | None:
        "Returns the affine matrix"
        if self.transform is None:
            return None
        else:
            return self.transform.affine

    #####
    # Bounding Box
    #####

    @property
    def bounds(self) -> BoundingBox | None:
        "Returns the bounding box"

        # Convert transform to bounds
        bounds = self._locator
        if isinstance(bounds, Transform):
            bounds = bounds.bounds(*self.shape)
        return self._get_locator(bounds)

    def _bound(self, name: str) -> Any | None:
        "Returns a bounding box attribute"
        if self.bounds is None:
            return None
        else:
            return getattr(self.bounds, name)

    @property
    def left(self) -> float | None:
        "Returns the spatial coordinate of the left edge"
        return self._bound("left")

    @property
    def right(self) -> float | None:
        "Returns the spatial coordinate of the right edge"
        return self._bound("right")

    @property
    def top(self) -> float | None:
        "Returns the spatial coordinate of the top edge"
        return self._bound("top")

    @property
    def bottom(self) -> float | None:
        "Returns the spatial coordinate of the bottom edge"
        return self._bound("bottom")

    @property
    def center(self) -> tuple[float, float] | None:
        "Returns the X,Y coordinate at the center of the bounding box"
        return self._bound("center")

    @property
    def center_x(self) -> float | None:
        "Returns the X coordinate at the center of the bounding box"
        return self._bound("center_x")

    @property
    def center_y(self) -> float | None:
        "Returns the Y coordinate at the center of the bounding box"
        return self._bound("center_y")

    @property
    def orientation(self) -> int | None:
        "Returns the Cartesian orientation of the bounding box"
        return self._bound("orientation")
