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

We recommend operational users begin with the "analyze" functions, which implements
a number of DEM analyses required for a basic hazard assessment. Other users may
be interested in the "pitfill", "flow_directions", "upslope_pixels", "upslope_sum",
and "relief" functions, which implement specific DEM analyses. Note that the
output of the "upslope_pixels" function can be combined with the DEM resolution
to give the total upslope (contributing) area. Also, the "upslope_sum" function
can be used to compute a variety of values, including the number of burned upslope
pixels, and the number of upslope debris basins.

In general, these functions operate on raster datasets, and users may provide 
input rasters in a variety of formats. Currently, the module supports:
    * A string indicating a raster file path,
    * A pathlib.Path object to a raster file,
    * A rasterio.DatasetReader object, or
    * A 2D numpy array (integer or floating)
Note that file-based rasters are loaded using rasterio, and so support nearly all
common raster file formats. You can find a complete list of supported formats
here: https://gdal.org/drivers/raster/index.html

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
    _validate_output    - Validate the path for a saved output raster
    _paths              - Return paths the rasters used by a TauDEM routine
    _run_taudem         - Runs a TauDEM routine as a subprocess
    _output             - Returns an output raster as a numpy 2D array or Path
"""

import rasterio
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from dfha import validate
from dfha.utils import write_raster, load_raster
from typing import Union, Optional, List, Literal, Tuple, Any, Sequence
from dfha.typing import Raster, ValidatedRaster, RasterArray, strs, Pathlike

# Type aliases
Option = Union[None, bool]  # None: Default, bool: User-specified
Output = Union[RasterArray, Path]
FlowSlopes = Tuple[Output, Output]
FlowOutput = Union[Output, FlowSlopes]
save = bool
SaveType = Union[None, save]  # (None is for inputs)
OutputPath = Union[None, Path]

# Configuration
verbose_by_default: bool = False  # Whether to print TauDEM messages to console
overwrite_by_default: bool = False  # Whether to overwrite files

#####
# User Functions
#####


def pitfill(
    dem: Raster,
    *,
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

    pitfill(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        dem: The digital elevation model raster being pitfilled
        path: The path to a file in which to save the pitfilled DEM
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).
        overwrite: True to allow saved output to replace existing files. False
            to prevent replacement. If unset, uses the default permission for
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
    pitfilled, save = _validate_output(path, overwrite)

    # Run using temporary files as necessary
    with TemporaryDirectory() as temp:
        dem, pitfilled = _paths(temp, [dem, pitfilled], [None, save], names)
        pitremove(dem, pitfilled, verbose)
        return _output(pitfilled, save)


def flow_directions(
    type: Literal["D8", "DInf"],
    pitfilled: Raster,
    *,
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

    flow_directions(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        type: Use "D8" for a D8 flow model. Use "DInf" for a D-Infinity flow model.
        pitfilled: The pitfilled DEM from which flow directions will be computed
        path: A path at which to save computed flow directions
        return_slopes: True to also return flow slopes. False (default) to only
            return flow-directions.
        slopes_path: A path at which to save computed flow slopes. Ignored if
            return_slopes is False.
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

    # Validate inputs
    verbose, overwrite = _options(verbose, overwrite)
    names = ["pitfilled", "flow_directions", "slopes"]
    [pitfilled] = _validate_inputs([pitfilled], names[0:1])
    flow, save = _validate_output(path, overwrite)
    if return_slopes:
        slopes, save_slopes = _validate_output(slopes_path, overwrite)
    else:
        slopes = None
        save_slopes = False

    # Get file paths, use temporary paths as necessary
    with TemporaryDirectory() as temp:
        pitfilled, flow, slopes = _paths(
            temp,
            [pitfilled, flow, slopes],
            [None, save, save_slopes],
            names,
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
    path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
    overwrite: Optional[bool] = None,
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

    upslope_area(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        flow_directions: The raster of D8 flow directions used to compute upslope.
            pixels. Flow numbers should proceed from 1 to 8, clockwise from right.
        path: The path to a file in which to save the upslope area.
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
    names = ["flow_directions", "upslope_area"]
    [flow] = _validate_inputs([flow_directions], names[0:1])
    area, save = _validate_output(path, overwrite)

    # Run using temp files as needed
    with TemporaryDirectory() as temp:
        flow, area = _paths(temp, [flow, area], [None, save], names)
        area_d8(flow, None, area, verbose)
        return _output(area, save)


def upslope_sum(
    flow_directions: Raster,
    weights: Raster,
    *,
    path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
    overwrite: Optional[bool] = None,
) -> Output:
    """
    upslope_sum  Computes a weighted sum of upslope pixels
    ----------
    upslope_sum(flow_directions, weights)
    Computes a weighted sum of upslope pixels. Each pixel is given a weight
    denoted by an associated weights raster. Returns the sum as a numpy 2D array.

    upslope_sum(..., *, path)
    upslope_sum(..., *, path, overwrite)
    Saves the upslope sum raster to file. Returns the absolute Path to the saved file
    rather than a numpy array. Use the "overwrite" option to allow/prevent saved
    output from replacing an existing file. If not set, uses the default overwrite
    permission for the module (initially set as False). If "path" is not provided,
    then "overwrite" is ignored.

    upslope_sum(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        flow_directions: D8 flow directions used to determine upslope sums. Flow
            numbers should proceed from 1 to 8, clockwise from right.
        weights: A weights raster, must have the same shape as the flow directions
            raster. Assigns a value to each pixel for the weighted sum.
        path: The path to a file in which to save the upslope sum.
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
    names = ["flow_directions", "weights", "upslope_sum"]
    [flow, weights] = _validate_inputs([flow_directions, weights], names[0:2])
    sum, save = _validate_output(path, overwrite)

    # Run using temp files as needed
    with TemporaryDirectory() as temp:
        flow, weights, sum = _paths(
            temp, [flow, weights, sum], [None, None, save], names
        )
        area_d8(flow, weights, sum, verbose)
        return _output(sum, save)


def relief(
    pitfilled: Pathlike,
    flow_directions: Pathlike,
    slopes: Pathlike,
    *,
    path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
    overwrite: Optional[bool] = None,
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

    relief(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        pitfilled: A pitfilled DEM raster
        flow_directions: A D-infinity flow direction raster. Must have the same
            shape as the pitfilled DEM.
        slopes: A D-infinity flow slopes raster. Must have the same shape as the
            pitfilled DEM.
        path: The path to the file in which to save the vertical relief raster.
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
    relief, save = _validate_output(path, overwrite)

    # Run using temp files as needed
    with TemporaryDirectory() as temp:
        pitfilled, flow, slopes, relief = _paths(
            temp, [pitfilled, flow, slopes, relief], [None, None, None, save], names
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
            if isinstance(raster, Path):
                with rasterio.open(raster) as data:
                    shape = (data.height, data.width)
            else:
                shape = raster.shape
    return rasters


def _validate_output(path: Any, overwrite: bool) -> Tuple[OutputPath, save]:
    """
    _validate_output  Validate and parse options for an output raster
    ----------
    _validate_output(path)
    Validates the Path for an output raster. A valid path may either be None (for
    returning the raster directly as an array), or convertible to a Path object.
    Returns the Path to the output file (which may be None), and a bool indicating
    whether the output raster should be saved to file.

    When a file path is provided, ensures the output file ends with a ".tif"
    extension. Files ending with ".tif" or ".tiff" (case-insensitive) are given
    to a ".tif" extension. Otherwise, appends ".tif" to the end of the file name.

    If the file already exists and overwrite is set to False, raises a FileExistsError.
    ----------
    Inputs:
        path: The user-provided Path to an output raster.

    Outputs:
        (None|pathlib.Path, bool): A 2-tuple. First element is the Path for the
            output raster - this may be None if not saving. Second element
            indicates whether the output raster should be saved to file.

    Raises:
        FileExistsError: If the file exists and overwrite=False
    """

    # Note whether saving to file
    if path is None:
        save = False
    else:
        save = True

        # If saving, get an absolute Path
        path = Path(path).resolve()

        # Optionally prevent overwriting
        if not overwrite and path.is_file():
            raise FileExistsError(
                "Output file already exists:\n\t{path}\n"
                'If you want to replace existing files, use the "overwrite" option.'
            )

        # Ensure a .tif extension
        extension = path.suffix
        if extension.lower() in [".tiff", ".tif"]:
            path = path.with_suffix(".tif")
        else:
            name = path.name + ".tif"
            path = path.with_name(name)
    return path, save


def _paths(
    temp: TemporaryDirectory,
    rasters: List[ValidatedRaster],
    save: Sequence[SaveType],
    names: Sequence[str],
) -> List[Path]:
    """
    _paths  Returns file paths for the rasters needed for a routine
    ----------
    _paths(temp, rasters, output_type, names)
    Returns a file path for each provided raster. If the raster has no associated
    file, returns the path to a temporary file.
    ----------
    Inputs:
        temp: A tempfile.TemporaryDirectory to hold temporary raster files.
        rasters: A list of validated rasters
        save: Whether each raster should be saved. Use a bool for output rasters,
            and None for input rasters.
        names: A name for each raster. Used to create temporary file names.

    Output:
        List[Path]: The absolute path to the file for each raster.
    """
    temp = Path(temp)
    indices = range(0, len(rasters))
    for r, raster, name, save in zip(indices, rasters, names, save):
        tempfile = temp / (name + ".tif")
        if save is None and not isinstance(raster, Path):
            write_raster(raster, tempfile)
            rasters[r] = tempfile
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
