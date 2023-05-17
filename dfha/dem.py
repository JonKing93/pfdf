"""
dem  Functions that implement DEM analyses
----------
The dem module provide functions that implement basic analyses on a Digital
Elevation Model (DEM). These include pitfilling, the calculation of flow
directions, upslope pixel counts, weighted sums of upslope pixels, and vertical
relief.

This module implements DEM analyses using the TauDEM package (specifically, the
TauDEM command-line interface). Documentation of TauDEM is available here:
https://hydrology.usu.edu/taudem/taudem5/documentation.html

We recommend users work with the "pitfill", "flow_directions", "upslope_pixels",
"upslope_sum", and "relief" functions, which implement specific DEM analyses.
Note that the "upslope_sum" function is generalizable to a number of analyses
useful for hazard assessment - for example, to compute the number of burned upslope
pixels, the number of developed upslope pixels, or the number of upslope debris
basins. We also note that the "relief" analysis is typically only needed when 
running the M3 model from Staley et al., 2017.

In general, these functions operate on raster datasets, and users may provide 
input rasters in a variety of formats. Currently, the module supports:
    * A string indicating a raster file path,
    * A pathlib.Path object to a raster file,
    * A rasterio.DatasetReader object, or
    * A 2D numpy array (integer or floating)
Note that file-based rasters are loaded using rasterio, and so support nearly all
common raster file formats. When possible, we recommend working with GeoTIFF formats,
but you can find a complete list of supported formats here: https://gdal.org/drivers/raster/index.html
When providing rasters as numpy arrays, it may be necessary to indicate a NoData
value in the array. See the NoData options for each function to provide these values.

Output rasters are returned as a numpy 2D by default, or are saved to a GeoTIFF
file if a path is provided. The module ensures that the output path always ends
in a "tif" extension - appending one to the file name, or converting ".tiff" to
".tif" as necessary. As such, the final output path may vary slightly from the
user-provided path. To accommodate this, the final Path to the raster is returned
as output when saving to file.

By default, this module suppresses TauDEM console output, and prevents saved
output files from replacing existing files. Users can set the module variables
"verbose_by_default" and "overwrite_by_default" to True to change this default
behavior. Alternatively, each function supports "verbose" and "overwrite" options,
which take precedence over the module's default behavior.

In addition to the standard user functions, this module includes the low-level
"pitremove", "flow_d8", "flow_dinf", "area_d8", and "relief_dinf" functions, 
which provide wrappers to the TauDEM commands used to implement the analyses. 
These functions are primarily intended for developers, and we recommend that
most users instead use the aforementioned high-level functions.

REQUIREMENTS:
Running this module requires:
    * Installing TauDEM 5.3
----------
User functions:
    pitfill             - Fills pits in a DEM
    flow_directions     - Computes D8 and D-Infinity flow directions and slopes
    upslope_pixels      - Computes the number of upslope pixels
    upslope_sum         - Computes a weighted sum of upslope pixels
    relief              - Computes the vertical component of the longest flow path

Low-level functions:
    pitremove           - Fills pits in a DEM
    flow_d8             - Computes D8 flow directions and slopes
    flow_dinf           - Computes D-infinity flow directions and slopes
    area_d8             - Computes D8 upslope area
    relief_dinf         - Computes vertical components of the longest flow path

Utilities:
    _options            - Determine verbosity and overwrite permissions for a routine
    _validate_inputs    - Validate user-provided input rasters
    _nodata             - Parses NoData values for numpy rasters
    _validate_d8        - Optionally validates D8 flow directions
    _validate_dinf      - Optionally validates D-infinity flow directions and slopes
    _paths              - Return paths for the rasters used by a TauDEM routine
    _run_taudem         - Runs a TauDEM routine as a subprocess
    _output             - Returns an output raster as a numpy 2D array or Path
"""

from numpy import ndarray, pi
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from dfha import validate
from dfha.utils import save_raster, load_raster, raster_shape, real
from typing import Union, Optional, List, Literal, Tuple, Any, Sequence
from dfha.typing import Pathlike, Raster, RasterArray, scalar, strs, ValidatedRaster

# Type aliases
Option = Union[None, bool]  # None: Default, bool: User-specified
Output = Union[RasterArray, Path]
FlowSlopes = Tuple[Output, Output]
FlowOutput = Union[Output, FlowSlopes]
SaveType = Union[None, bool]  # (None is for inputs)
nodata = Union[None, scalar]

# Configuration
verbose_by_default: bool = False  # Whether to print TauDEM messages to console
overwrite_by_default: bool = False  # Whether to overwrite files

#####
# User Functions
#####


def pitfill(
    dem: Raster,
    *,
    nodata: Optional[scalar] = None,
    path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
    overwrite: Optional[bool] = None,
) -> Output:
    """
    pitfill  Fills pits (depressions) in a DEM
    ----------
    pitfill(dem)
    Runs the TauDEM pitfilling routine on the input DEM. Returns the pitfilled
    DEM as a numpy 2D array.

    pitfill(..., *, path)
    pitfill(..., *, path, overwrite)
    Saves the pitfilled DEM to file. Returns the absolute Path to the saved file
    rather than a numpy array. Use the "overwrite" option to allow/prevent saved
    output from replacing an existing file. If not set, uses the default overwrite
    permission for the module (initially set as False). If "path" is not provided,
    then "overwrite" is ignored.

    pitfill(..., *, nodata)
    Optionally indicates a NoData value when the DEM is a numpy array. Without
    this option, all values in a numpy array are treated as valid. The nodata
    value will be converted to the same dtype as the DEM. If the DEM is a file-based
    raster, this option is ignored and the NoData value is instead determined from
    the file metadata.

    pitfill(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        dem: The digital elevation model raster being pitfilled.
        path: The path to a file in which to save the pitfilled DEM
        overwrite: True to allow saved output to replace existing files. False
            to prevent replacement. If unset, uses the default permission for
            the module (initially set as False).
        nodata: A NoData value for the DEM when it is a numpy array.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array | pathlib.Path: The pitfilled DEM, or path to a saved
            pitfilled DEM.

    Saves:
        Optionally saves the pitfilled DEM to a path matching the "path" input
    """

    # Validate
    verbose, overwrite = _options(verbose, overwrite)
    names = ["dem", "pitfilled"]
    [dem] = _validate_inputs([dem], names[0:1])
    nodata = _nodata([nodata], ["nodata"], [dem])
    pitfilled, save = validate.output_path(path, overwrite)

    # Run using temporary files as necessary
    with TemporaryDirectory() as temp:
        dem, pitfilled = _paths(temp, [dem, pitfilled], [None, save], names, nodata)
        pitremove(dem, pitfilled, verbose)
        return _output(pitfilled, save)


def flow_directions(
    type: Literal["D8", "DInf"],
    pitfilled: Raster,
    *,
    nodata: Optional[scalar] = None,
    path: Optional[Pathlike] = None,
    return_slopes: Optional[bool] = False,
    slopes_path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
    overwrite: Optional[bool] = None,
) -> FlowOutput:
    """
    flow_directions  Computes D8 or D-Infinity flow directions and slopes
    ----------
    flow_directions(type, pitfilled)
    Computes D8 or D-Infinity flow directions from a pitfilled DEM. Returns the
    flow directions as a numpy 2D array. D8 flow directions are numbered from
    1 to 8 proceeding clockwise from right.

    flow_directions(..., *, path)
    flow_directions(..., *, path, overwrite)
    Saves the flow directions to file. Returns the absolute Path to the saved file
    rather than a numpy array. Use the "overwrite" option to allow/prevent saved
    rasters from replacing an existing file. If not set, uses the default overwrite
    permission for the module (initially set as False).

    flow_directions(..., *, return_slopes=True)
    flow_directions(..., *, return_slopes=True, slopes_path)
    flow_directions(..., *, return_slopes=True, slopes_path, overwrite)
    Also returns flow slopes. The output will be a 2-tuple - the first element is
    the flow-directions and the second element is the flow-slopes. If "slopes_path"
    is provided, save the slopes and returns the Path to the saved raster. Otherwise,
    returns the slopes as a numpy 2D array. The "overwrite" option can also be
    used to permit/allow saved flow slopes to replace existing files.

    flow_directions(..., *, nodata)
    Optionally indicates a NoData value for when the pitfilled DEM is a numpy array.
    Without this option, all values in an input numpy array are treated as valid.
    The nodata value will be converted to the dtype of the pitfilled DEM. If
    the pitfilled DEM is a file-based raster, this option is ignored and the NoData
    value is instead determined from the file metadata.

    flow_directions(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        type: Use "D8" for a D8 flow model. Use "DInf" for a D-Infinity flow model.
        pitfilled: The pitfilled DEM from which flow directions will be computed.
        path: A path at which to save computed flow directions
        return_slopes: True to also return flow slopes. False (default) to only
            return flow-directions.
        slopes_path: A path at which to save computed flow slopes. Ignored if
            return_slopes is False.
        nodata: A NoData value for the pitfilled DEM when it is a numpy array.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array | pathlib.Path: The flow directions or Path to saved flow
            directions. (If not returning flow slopes).

        2-Tuple (flow_directions, flow_slopes): If also returning flow slopes,
            returns a 2-tuple whose first element is the flow directions and
            second element is the flow slopes. Each output raster may either be
            a numpy 2D array or Path, depending on whether the associated path
            was provided.

    Saves:
        Optionally saves flow-directions to a path matching the "path" input.
        Optionally saves flow slopes to a path matching the "slopes_path" input.
    """

    # Validate standard inputs
    verbose, overwrite = _options(verbose, overwrite)
    names = ["pitfilled", "flow_directions", "slopes"]
    [pitfilled] = _validate_inputs([pitfilled], names[0:1])
    nodata = _nodata([nodata], ["nodata"], [pitfilled])
    flow, save = validate.output_path(path, overwrite)

    # Get flow-slope options and path
    if return_slopes:
        slopes, save_slopes = validate.output_path(slopes_path, overwrite)
    else:
        slopes = None
        save_slopes = False

    # Get file paths, use temporary paths as necessary
    with TemporaryDirectory() as temp:
        pitfilled, flow, slopes = _paths(
            temp, [pitfilled, flow, slopes], [None, save, save_slopes], names, nodata
        )

        # Run the appropriate flow model
        if type == "D8":
            flow_model = flow_d8
        elif type == "DInf":
            flow_model = flow_dinf
        flow_model(pitfilled, flow, slopes, verbose)

        # ALways return flow. Optionally return slopes
        flow = _output(flow, save)
        if return_slopes:
            slopes = _output(slopes, save_slopes)
            return flow, slopes
        else:
            return flow


def upslope_pixels(
    flow_directions: Raster,
    *,
    nodata: Optional[scalar] = None,
    path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
    overwrite: Optional[bool] = None,
    check: bool = True,
) -> Output:
    """
    upslope_pixels  Computes the number of upslope pixels over a DEM
    ----------
    upslope_pixels(flow_directions)
    Uses D8 flow directions to compute the number of upslope pixels for a DEM.
    Upslope pixel counts can be combined with the DEM resolution to give the
    total upslope (contributing) area for the DEM. Returns the upslope pixel
    counts as a numpy 2D array.

    upslope_pixels(..., *, path)
    upslope_pixels(..., *, path, overwrite)
    Saves the upslope pixel raster to file. Returns the absolute Path to the saved file
    rather than a numpy array. Use the "overwrite" option to allow/prevent saved
    output from replacing an existing file. If not set, uses the default overwrite
    permission for the module (initially set as False). If "path" is not provided,
    then "overwrite" is ignored.

    upslope_pixels(..., *, nodata)
    Optionally indicates a NoData value for when the flow directions are a numpy array.
    Without this option, all values in an input numpy array are treated as valid.
    The nodata value will be converted to the dtype of the flow directions. If
    the flow directions are a file-based raster, this option is ignored and the
    NoData value is instead determined from the file metadata.

    upslope_pixels(..., *, check=False)
    Disables the validation of D8 flow directions. When enabled, the validation
    checks that flow directions are integers on the interval from 1 to 8 (excepting
    NoData values). Disabling this check can speed up processing of large rasters,
    but may give unexpected results if the flow-directions raster contains
    invalid values.

    upslope_pixels(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        flow_directions: The raster of D8 flow directions used to compute upslope.
            pixels. Flow numbers should proceed from 1 to 8, clockwise from right.
        path: The path to a file in which to save the upslope area.
        nodata: A NoData value for the flow directions when they are a numpy array.
        check: True to validate flow-direction numbers. False to disable this check.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array | pathlib.Path: The upslope pixel raster as an array or
            the Path to a saved upslope pixel raster.

    Saves:
        Optionally saves upslope area to a path matching the "path" input.
    """

    # Validate
    verbose, overwrite = _options(verbose, overwrite)
    names = ["flow_directions", "upslope_pixels"]
    [flow] = _validate_inputs([flow_directions], names[0:1])
    nodata = _nodata([nodata], ["nodata"], [flow])
    area, save = validate.output_path(path, overwrite)
    _validate_d8(check, flow, nodata[0])

    # Run using temp files as needed
    with TemporaryDirectory() as temp:
        flow, area = _paths(temp, [flow, area], [None, save], names, nodata)
        area_d8(flow, None, area, verbose)
        return _output(area, save)


def upslope_sum(
    flow_directions: Raster,
    values: Raster,
    *,
    flow_nodata: Optional[scalar] = None,
    values_nodata: Optional[scalar] = None,
    path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
    overwrite: Optional[bool] = None,
    check: bool = True,
) -> Output:
    """
    upslope_sum  Computes a weighted sum of upslope pixels
    ----------
    upslope_sum(flow_directions, values)
    Computes a sum over upslope pixels. Each pixel is given a value denoted by
    the "values" raster. Returns the sum raster as a numpy 2D array.

    upslope_sum(..., *, path)
    upslope_sum(..., *, path, overwrite)
    Saves the upslope sum raster to file. Returns the absolute Path to the saved file
    rather than a numpy array. Use the "overwrite" option to allow/prevent saved
    output from replacing an existing file. If not set, uses the default overwrite
    permission for the module (initially set as False). If "path" is not provided,
    then "overwrite" is ignored.

    upslope_sum(..., *, flow_nodata)
    upslope_sum(..., *, values_nodata)
    Optionally indicate NoData values for when the flow directions or pixel values
    are a numpy array. Without these options, all values in an input numpy array
    are treated as valid. The nodata value will be converted to the dtype of
    associated raster. If an input raster is file-based, the associated nodata
    value is ignored and NoData values are determined from the file metadata.

    upslope_sum(..., *, check=False)
    Disables the validation of D8 flow directions. When enabled, the validation
    checks that flow directions are integers on the interval from 1 to 8 (excepting
    NoData values). Disabling this check can speed up processing of large rasters,
    but may give unexpected results if the flow-directions raster contains
    invalid values.

    upslope_sum(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        flow_directions: D8 flow directions used to determine upslope sums. Flow
            numbers should proceed from 1 to 8, clockwise from right.
        values: A raster indicating the value of each pixel to use in the sum.
            Must have the same shape as the flow directions raster.
        path: The path to a file in which to save the upslope sum.
        flow_nodata: A NoData value for the flow directions when they are a numpy array.
        values_nodata: A NoData value for the pixel values when they are a numpy array.
        check: True to validate flow-direction numbers. False to disable this check.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array | pathlib.Path: The upslope sum raster or the Path to a
            saved upslope sum raster.

    Saves:
        Optionally saves the upslope sum raster to a path matching the "path" input.
    """

    # Validate
    verbose, overwrite = _options(verbose, overwrite)
    names = ["flow_directions", "values", "upslope_sum"]
    [flow, values] = _validate_inputs([flow_directions, values], names[0:2])
    nodata = _nodata(
        [flow_nodata, values_nodata],
        ["flow_nodata", "values_nodata"],
        [flow, values],
    )
    sum, save = validate.output_path(path, overwrite)
    _validate_d8(check, flow, nodata[0])

    # Run using temp files as needed
    with TemporaryDirectory() as temp:
        flow, values, sum = _paths(
            temp,
            [flow, values, sum],
            [None, None, save],
            names,
            nodata,
        )
        area_d8(flow, values, sum, verbose)
        return _output(sum, save)


def msum(flow_directions, values, mask):
    verbose, overwrite = _options(verbose, overwrite)
    names = ['flow_directions', 'values', 'mask']
    [flow, values] = _validate_inputs([flow_directions, values], names[0:2])
    nodata = _nodata(
        [flow_nodata, values_nodata, mask_nodata],
        ["flow_nodata", "values_nodata", "mask_nodata"],
        [flow, values, mask],
    )
    sum, save = validate.output_path(path, overwrite)

    mask = validate.raster(mask, 'mask', shape=flow.shape, dtype=mask_dtypes, load=False)
    if check:
        mask = load_raster(mask, numpy_nodata=nodata[2], nodata_to=0)
        mask = validate.mask(mask, 'mask')
    _validate_d8(check, flow, nodata[0])

    values = values * mask





def relief(
    pitfilled: Pathlike,
    flow_directions: Pathlike,
    slopes: Pathlike,
    *,
    pitfilled_nodata: Optional[scalar] = None,
    flow_nodata: Optional[scalar] = None,
    slopes_nodata: Optional[scalar] = None,
    path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
    overwrite: Optional[bool] = None,
    check: bool = True,
) -> Output:
    """
    relief  Computes the vertical relief along the longest flow path
    ----------
    relief(pitfilled, flow_directions, slopes)
    Computes the vertical relief along the longest flow path. Requires D-infinity
    flow directions and slopes. Returns the relief raster as a numpy 2D array.

    relief(..., *, path)
    relief(..., *, path, overwrite)
    Saves the relief raster to file. Returns the absolute Path to the saved file
    rather than a numpy array. Use the "overwrite" option to allow/prevent saved
    output from replacing an existing file. If not set, uses the default overwrite
    permission for the module (initially set as False). If "path" is not provided,
    then "overwrite" is ignored.

    relief(..., *, pitfilled_nodata)
    relief(..., *, flow_nodata)
    relief(..., *, slopes_nodata)
    Optionally indicate NoData values for when the pitfilled DEM, flow directions,
    and/or flow slopes are numpy arrays. Without these options, all values in the
    associated input numpy arrays are treated as valid. Each nodata value will be
    converted to the dtype of the associated input raster. If an input raster
    is file-based, the associated nodata value is ignored.

    relief(..., *, check=False)
    Disables validation of flow-directions and slopes. When enabled, the validation
    checks that (1) flow directions are on the interval from 0 to 2*pi, and
    (2) flow slopes are positive. (Excepting NoData values). Disabling this check
    can speed the processing of large rasters, but may give unexpected results
    if the rasters contain invalid values.

    relief(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        pitfilled: A pitfilled DEM raster.
        flow_directions: A D-infinity flow direction raster. Must have the same
            shape as the pitfilled DEM.
        slopes: A D-infinity flow slopes raster. Must have the same shape as the
            pitfilled DEM.
        path: The path to the file in which to save the vertical relief raster.
        pitfilled_nodata: A NoData value for the pitfilled DEM when it is a numpy array.
        flow_nodata: A NoData value for the flow_directions when they are a numpy array.
        slopes_nodata: A NoData value for the flow slopes when they are a numpy array.
        check: True to validate flow-directions and slopes. False to disable the checks.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array: The vertical relief raster.
        pathlib.Path: The Path to a saved vertical relief raster.

    Saves:
        Optionally saves the vertical relief to a path matching the "path" input.
    """

    # Validate
    verbose, overwrite = _options(verbose, overwrite)
    names = ["pitfilled", "flow_directions", "slopes", "relief"]
    [pitfilled, flow, slopes] = _validate_inputs(
        [pitfilled, flow_directions, slopes], names[0:3]
    )
    nodata = _nodata(
        [pitfilled_nodata, flow_nodata, slopes_nodata],
        ["pitfilled_nodata", "flow_nodata", "slopes_nodata"],
        [pitfilled, flow, slopes],
    )
    relief, save = validate.output_path(path, overwrite)
    _validate_dinf(check, flow, nodata[1], slopes, nodata[2])

    # Run using temp files as needed
    with TemporaryDirectory() as temp:
        pitfilled, flow, slopes, relief = _paths(
            temp,
            [pitfilled, flow, slopes, relief],
            [None, None, None, save],
            names,
            nodata,
        )
        relief_dinf(pitfilled, flow, slopes, relief, verbose)
        return _output(relief, save)


#####
# Low Level
#####


def pitremove(dem_path: Path, pitfilled_path: Path, verbose: bool) -> None:
    """
    pitremove  Runs the TauDEM PitRemove routine
    ----------
    pitremove(dem_path, pitfilled_path, verbose)
    Runs the TauDEM pit filling routine on a input DEM. Saves the output
    pitfilled DEM to the indicated path. Optionally prints TauDEM messages to
    the console.
    ----------
    Inputs:
        dem_path: The absolute Path object for the input DEM
        pitfilled_path: The absolute Path object for the output
            pitfilled DEM.
        verbose: True if TauDEM messages should be printed to the console.
            False if the messages should be suppressed.

    Outputs: None

    Saves:
        A file matching the "pitfilled" path
    """

    pitremove = f"PitRemove -z {dem_path} -fel {pitfilled_path}"
    _run_taudem(pitremove, verbose)


def flow_d8(
    pitfilled_path: Path, flow_directions_path: Path, slopes_path: Path, verbose: bool
) -> None:
    """
    flow_d8  Runs the TauDEM D8 flow direction routine
    ----------
    flow_d8(pitfilled_path, flow_directions_path, slopes_path, verbose)
    Calculates flow directions and slopes from a pitfilled DEM using a D8 flow
    model. Saves the output flow directions and slopes to the indicated paths.
    Optionally prints TauDEM messages to the console.
    ----------
    Inputs:
        pitfilled_path: The absolute Path to the pitfilled DEM being analyzed.
        flow_directions_path: The absolute Path for the output flow directions
        slopes_path: The absolute Path for the output slopes
        verbose: True if TauDEM messages should be printed to console.
            False if these messages should be suppressed.

    Outputs: None

    Saves:
        Files matching the "flow_directions" and "slopes" paths.
    """

    flow_d8 = (
        f"D8FlowDir -fel {pitfilled_path} -p {flow_directions_path} -sd8 {slopes_path}"
    )
    _run_taudem(flow_d8, verbose)


def flow_dinf(
    pitfilled_path: Path, flow_directions_path: Path, slopes_path: Path, verbose: bool
) -> None:
    """
    flow_dinf  Runs the TauDEM D-Infinity flow direction routine
    ----------
    flow_dinf(pitfilled_path, flow_directions_path, slopes_path, verbose)
    Calculates flow directions and slopes from a pitfilled DEM using a
    D-infinity flow model. Saves the output flow directions and slopes to the
    indicated paths. Optionally prints TauDEM messages to the console.
    ----------
    Inputs:
        pitfilled_path: The absolute Path to the pitfilled DEM being analyzed.
        flow_directions_path: The absolute Path for the output flow directions
        slopes_path: The absolute Path for the output slopes
        verbose: True if TauDEM messages should be printed to console.
            False if these messages should be suppressed.

    Outputs: None

    Saves:
        Files matching the "flow_directions" and "slopes" paths.
    """

    flow_dinf = f"DInfFlowDir -fel {pitfilled_path} -ang {flow_directions_path} -slp {slopes_path}"
    _run_taudem(flow_dinf, verbose)


def area_d8(
    flow_directions_path: Path,
    weights_path: Union[Path, None],
    area_path: Path,
    verbose: bool,
) -> None:
    """
    area_d8  Runs the TauDEM D8 upslope area routine
    ----------
    area_d8(flow_directions_path, weights_path=None, area_path, verbose)
    Computes upslope area (also known as contributing area) using a D8 flow model.
    All raster pixels are given an equal area of 1. Saves the output upslope
    area to the indicated path. Optionally prints TauDEM messages to the console.

    area_d8(flow_directions_path, weights_path, area_path, verbose)
    Computes weighted upslope area. The area of each raster pixel is set to the
    corresponding value in the weights raster.
    ----------
    Inputs:
        flow_directions_path: The absolute Path for the input D8 flow directions.
        weights_path: The absolute Path to the input raster holding area weights
            for each pixel. If None, computes unweighted upslope area.
        area: The absolute Path to the output upslope area
        verbose: True if TauDEM messages should be printed to the console.
            False to suppress these messages.

    Outputs: None

    Saves:
        A file matching the "area" path.
    """

    area_d8 = f"AreaD8 -p {flow_directions_path} -ad8 {area_path} -nc"
    if weights_path is not None:
        area_d8 += f" -wg {weights_path}"
    _run_taudem(area_d8, verbose)


def relief_dinf(
    pitfilled_path: Path,
    flow_directions_path: Path,
    slopes_path: Path,
    relief_path: Path,
    verbose: bool,
) -> None:
    """
    relief_dinf  Computes the vertical component of the longest flow path
    ----------
    relief_dinf(pitfilled_path, flow_directions_path, slopes_path, relief_path, verbose)
    Computes the vertical component of the longest flow path. This analysis
    requires an input pitfilled DEM, and D-Infinity flow directions and slopes.
    The routine is set to account for edge contamination. Uses a threshold of
    0.49 so that computed relief mimics the results for a D8 flow model. Saves
    the computed length to the indicated path. Optionally prints TauDEM messages
    to the console.
    ----------
    Inputs:
        pitfilled_path: The absolute Path to the input pitfilled DEM
        flow_directions_path: The absolute Path to the input D-infinity flow directions
        slopes_path: The absolute Path to the input D-infinity slopes
        relief_path: The absolute Path to the output D8 relief
        verbose: True to print TauDEM messages to the console. False to
            suppress these messages.

    Outputs: None

    Saves:
        A file matching the "relief" path.
    """

    # Run the command. The "-m max v" computes the (v)ertical component of the
    # longest (max)imum flow path. The "-thresh 0.49" option mimics results for a
    #  D8 flow model. The "-nc" flag causes the routine to account for edge contamination.
    relief = (
        f"DinfDistUp -fel {pitfilled_path} -ang {flow_directions_path}"
        + f" -slp {slopes_path} -du {relief_path} -m max v -thresh 0.49 -nc"
    )
    _run_taudem(relief, verbose)


#####
# Utilities
#####


def _options(verbose: Option, overwrite: Option) -> Tuple[bool, bool]:
    """
    _options  Parses the verbosity and overwrite setting for a routine
    ----------
    _options(verbose, overwrite)
    Parses the verbosity and file overwrite settings for a routine. The option is
    not altered if it is a bool. If the option is None (i.e. not set by the user),
    sets the option to the default value for the module. The default verbosity is
    set by the verbose_by_default variable. Default overwrite setting is set by
    overwrite_by_default. Returns the final verbosity and overwrite settings.
    ----------
    Inputs:
        verbose: The initial state of the verbosity option
        overwrite: The initial state of the overwrite option

    Outputs:
        (bool, bool): The first element is the verbosity setting, and the second
            is the overwrite setting.
    """
    if verbose is None:
        verbose = verbose_by_default
    if overwrite is None:
        overwrite = overwrite_by_default
    return verbose, overwrite


def _validate_inputs(rasters: List[Any], names: Sequence[str]) -> List[ValidatedRaster]:
    """
    _validate_inputs  Validates user provided input rasters
    ----------
    _validate_inputs(rasters, names)
    Checks that inputs are valid rasters. If multiple rasters are provided,
    checks that all rasters have the same shape. Does not load file-based rasters
    into memory.
    ----------
    Inputs:
        rasters: The user-provided input rasters
        names: The names of the rasters for use in error messages.

    Outputs:
        List[numpy 2D array | Path]: The validated rasters.
    """

    # Validate each raster. First raster may be any shape
    shape = None
    nrasters = len(rasters)
    for r, raster, name in zip(range(0, nrasters), rasters, names):
        rasters[r] = validate.raster(raster, name, shape=shape, load=False)

        # Get the shape from the first raster
        if nrasters > 1 and r == 0:
            shape = raster_shape(raster)
    return rasters


def _nodata(
    nodata: List[Any],
    names: Sequence[str],
    rasters: Sequence[ValidatedRaster],
) -> List[nodata]:
    """
    _nodata  Validates and parses NoData values for input numpy rasters
    ----------
    _nodata(nodata, names, rasters)
    Validates nodata values for input rasters that are numpy arrays. Ensures each
    NoData value is the same dtype as the associated raster. Returns the validated
    NoData values as a list.
    ----------
    Inputs:
        nodata: User-provided nodata values for the input rasters
        names: The names of the nodata variables for use in error messages
        rasters: The validated input rasters

    Outputs:
        List[None | real-valued scalar]: The validated NoData values
    """

    indices = range(0, len(nodata))
    for k, value, name, raster in zip(indices, nodata, names, rasters):
        if isinstance(raster, ndarray) and value is not None:
            value = validate.scalar(value, name, real)
            nodata[k] = value.astype(raster.dtype)
    return nodata


def _validate_d8(check: bool, flow: ValidatedRaster, nodata: nodata) -> None:
    """
    _validate_d8  Optionally validates D8 flow directions
    ----------
    _validate_d8(check, flow, nodata)
    Optionally checks that D8 flow direction values are valid. Valid D8 flow
    directions are integers from 1 to 8.  Set check=False to disable validation.
    Raises a ValueError if the validation fails.
    ----------
    Inputs:
        check: True to validate. False to skip validation
        flow: A D8 flow-directions raster
        nodata: The NoData value for numpy arrays
    """
    if check:
        flow = load_raster(flow, numpy_nodata=nodata, nodata_to=1)
        validate.flow(flow, "flow_directions")


def _validate_dinf(
    check: bool,
    flow: ValidatedRaster,
    flow_nodata: nodata,
    slopes: ValidatedRaster,
    slopes_nodata: nodata,
) -> None:
    """
    _validate_dinf  Optionally validates D-Infinity flow directions and slopes
    ----------
    _validate_dinf(check, flow, flow_nodata, slopes, slopes_nodata)
    Optionally checks that D-Infinity flow directions and slopes are valid.
    Valid flow directions are on the interval from 0 to 2pi. Valid slopes are
    positive. Set check=False to disable validation. Raises a ValueError if
    validation fails.
    ----------
    Inputs:
        check: True to validate. False to skip validation
        flow: A D-infinity flow directions raster
        flow_nodata: NoData value for numpy flow directions
        slopes: A D-infinity flow slopes raster
        slopes_nodata: NoData value for numpy flow slopes
    """
    if check:
        flow = load_raster(flow, numpy_nodata=flow_nodata, nodata_to=0)
        validate.inrange(flow, "flow_directions", min=0, max=2 * pi)
        slopes = load_raster(slopes, numpy_nodata=slopes_nodata, nodata_to=0)
        validate.positive(slopes, "slopes", allow_zero=True)


def _paths(
    temp: TemporaryDirectory,
    rasters: List[ValidatedRaster],
    save: Sequence[SaveType],
    names: Sequence[str],
    nodata: Sequence[nodata],
) -> List[Path]:
    """
    _paths  Returns file paths for the rasters needed for a routine
    ----------
    _paths(temp, rasters, output_type, names, nodatas)
    Returns a file path for each provided raster. If the raster has no associated
    file, returns the path to a temporary file.
    ----------
    Inputs:
        temp: A tempfile.TemporaryDirectory to hold temporary raster files.
        rasters: A list of validated rasters
        save: Whether each raster should be saved. Use a bool for output rasters,
            and None for input rasters.
        names: A name for each raster. Used to create temporary file names.
        nodatas: A NoData value for each input raster. Should have one element
            per None value in the "save" input.

    Output:
        List[Path]: The absolute path to the file for each raster.
    """

    # Setup variables
    temp = Path(temp)
    indices = range(0, len(rasters))
    nOutputs = len(rasters) - len(nodata)
    nodata = nodata + [None] * nOutputs

    # Iterate through rasters and get temporary file names
    for r, raster, name, save, nodata in zip(indices, rasters, names, save, nodata):
        tempfile = temp / (name + ".tif")

        # Write input arrays to a temp file.
        if save is None and not isinstance(raster, Path):
            save_raster(raster, tempfile, nodata)
            rasters[r] = tempfile

        # Use a temp file for output rasters returned as arrays
        elif save == False:
            rasters[r] = tempfile
    return rasters


def _run_taudem(command: strs, verbose: bool) -> None:
    """
    _run_taudem  Runs a TauDEM command as a subprocess
    ----------
    _run_taudem(command, verbose)
    Runs a TauDEM command as a subprocess. If verbose=True, prints TauDEM
    messages to the console. If verbose=False, suppresses these messages. Raises
    a CalledProcessError if the TauDEM process does not complete successfully
    (i.e. the process returns an exit code not equal to 0).
    ----------
    Inputs:
        command: The arguments used to run a TauDEM command
        verbose: True if TauDEM messages should be printed to the
            console. False if these messages should be suppressed.

    Raises:
        CalledProcessError: If the TauDEM process returns an exit code not equal
            to 0.

    Saves:
        The various output files associated with the TauDEM command.

    Outputs: None
    """

    return subprocess.run(command, capture_output=not verbose, check=True)


def _output(raster: Path, save: bool) -> Output:
    """
    _output  Returns the final output form of a TauDEM output raster.
    ----------
    _output(raster, save)
    If saving the raster to file, returns the absolute Path to the file. If not
    saving, returns the rasters as a numpy 2D array.
    ----------
    Inputs:
        raster: The absolute Path to a TauDEM output raster
        save: True if returning the Path to a saved raster. False if returning a
            numpy 2D array.

    Outputs:
        pathlib.Path | numpy 2D array: The raster as a numpy array, or the Path
            to a saved raster.
    """
    if not save:
        raster = load_raster(raster)
    return raster
