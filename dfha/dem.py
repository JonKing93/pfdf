"""
dem  Functions that implement DEM analyses
----------
The dem module provide functions that implement basic analyses on a Digital
Elevation Model (DEM). These include pitfilling, and the calculation of flow
directions, upslope areas, and vertical relief.

This module implements DEM analyses using the TauDEM package (specifically, the
TauDEM command-line interface). Documentation of TauDEM is available here:
https://hydrology.usu.edu/taudem/taudem5/documentation.html

We recommend most users begin with the "analyze" function, which implements all
the DEM analyses required for a basic hazard assessment. Users may also be
interested in the "pitfill", "flow_directions", "upslope_area", "upslope_burn",
"upslope_basins", and "relief" functions, which implement individual pieces of
this overall analysis. (Note that upslope_basins and upslope_burn are specialized
versions of upslope_area. In general, you can use upslope_area to implement both
weighted and unweighted upslope area routines).

In general, the functions in this module require various input rasters and
compute rasters as outputs. The module follows the raster file format
conventions of TauDEM: input rasters may use nearly any raster file format, but
outputs will always use a GeoTIFF format. Specifically, the module supports any
input raster format that can be read by the GDAL library. For a complete list of
supported formats, see: https://gdal.org/drivers/raster/index.html

In addition to the user functions, this module includes the low-level 
"pitremove", "flow_d8", "flow_dinf", "area_d8", and "relief_dinf" functions, 
which provide wrappers to the TauDEM commands used to implement the analyses. 
These functions are primarily intended for developers, and we recommend that
most users instead use the aforementioned high-level functions.

The rasters produced by this module are often used to help delineate a
stream network. As such, a suggested workflow for hazard assessment users is as
follows:
    * Acquire DEM data
    *** Run this module
    * Delineate a stream network
    * Filter the network to model-worthy drainages

REQUIREMENTS:
Running this module requires:
    * Installing TauDEM 5.3
----------
User functions:
    analyze             - Implements all DEM analyses required for standard hazard assessment
    pitfill             - Fills pits in a DEM
    flow_directions     - Computes D8 and D-Infinity flow directions and slopes
    upslope_area        - Computes upslope (contributing) area
    upslope_burn        - Computes total upslope burned area
    upslope_basins      - Computes the number of upslope debris-retention basins
    relief              - Computes the vertical component of the longest flow path

Low-level functions:
    pitremove           - Fills pits in a DEM
    flow_d8             - Computes D8 flow directions and slopes
    flow_dinf           - Computes D-infinity flow directions and slopes
    area_d8             - Computes D8 upslope area
    relief_dinf         - Computes vertical components of the longest flow path

Utilities:
    _verbosity          - Determines the verbosity setting for a routine
    _input_paths        - Returns the absolute Path for an input file
    _output_path        - Returns the absolute Path for an output file
    _temporary          - Returns an absolute Path for a temporary output file
    _run_taudem         - Runs a TauDEM routine as a subprocess
    _setup              - Prepares the Path dict for a DEM analysis
    _output_dict        - Builds the output Path dict for a DEM analysis
"""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from dfha import validate
from dfha.utils import write_raster, load_raster
from typing import Union, Optional, List, Literal, Tuple, Dict, Any, Sequence
from dfha.typing import Raster, ValidatedRaster, RasterArray, strs, Pathlike, PathDict

# Type aliases
Output = Union[RasterArray, Path]
FlowSlopes = Tuple[Output, Output]
FlowOutput = Union[Output, FlowSlopes]
OutputOption = Literal["default", "saved", "all"]
OutputType = Union[None, bool]

# Configuration
verbose_by_default: bool = False  # Whether to print TauDEM messages to console

# Types of files in a DEM analysis
_inputs = ["dem", "isburned"]
_intermediate = ["pitfilled", "flow_directions_dinf", "slopes_dinf"]
_final = ["flow_directions", "total_area", "burned_area", "relief"]
_basins = ["isbasin", "upslope_basins"]

# Type aliases
InputPath = Union[Pathlike, None]


#####
# Operational
#####
def analyze(
    paths: Dict[str, Pathlike],
    *,
    outputs: OutputOption = "default",
    verbose: Optional[bool] = None,
) -> PathDict:
    """
    analyze  Conducts all DEM analyses for a standard hazard assessment
    ----------
    analyze(paths)
    Conducts all DEM analyses required for a standard hazard assessment. Uses
    various routines from the TauDEM package. Begins by pitfilling a DEM and
    then computes flow directions and slopes. Uses the results of these initial
    analyses to compute total upslope area, total burned upslope area, and the
    vertical relief of the longest flow path. Optionally computes debris-basin
    flow routing. Returns a dict with the absolute Paths to the computed output
    files.

    The "paths" input is a dict mapping analysis files to their paths. Each file
    path may be either a pathlib.Path object or a string. The "paths" dict has
    both mandatory and optional keys (summarized below). Mandatory keys are for
    files essential to the analysis. These include 'dem', 'isburned',
    'flow_directions', 'total_area', 'burned_area', and 'relief'. (See below for
    descriptions of these keys).

    If "paths" only contains the mandatory keys, then the analysis will not
    compute debris-basin flow routing. You can enable flow routing by
    including the two optional keys 'isbasin' and 'upslope_basins' in the paths
    input. If you include the 'isbasin' key, but its value is None, then the
    upslope_basins key will be ignored and the analysis will not implement
    debris basin flow routing.

    By default, the function will delete intermediate output files used in the
    analysis. These consist of the pitfilled DEM, and the D-infinity flow
    directions and slopes. You can save an intermediate file by including its
    key in the "paths" input, along with a path. The keys for these optional
    files are 'pitfilled', 'flow_directions_dinf', and 'slopes_dinf'. If you
    include one of these keys but its value is None, then the file will be
    deleted as usual.

    By default, the function will return a dict with the absolute Paths for the
    computed output rasters. This will always include the D8 flow directions,
    total upslope area, total burned upslope area, vertical relief, and (if debris
    basin flow routing is enabled) the computed number of upslope debris basins.
    The keys for these outputs will match the corresponding keys in the "paths" input.

    analyze(..., *, outputs= "default" | "saved" | "all")
    Indicates the Paths that should be included in the output dict.
    If outputs="default", the dict includes the Paths of the D8 flow directions,
    total upslope area, total burned upslope area, vertical relief, and (if flow
    routing was enabled) the number of upslope debris basins. If outputs="saved",
    includes the keys for all saved output files. These include the default keys,
    as well as any saved intermediate output files. If outputs="all", includes
    keys for all possible output files produced by this function. This includes
    the default outputs, intermediate outputs, and the optional debris-basin output.
    If a file was not saved during the analysis, then the value of its key
    will be None.

    analyze(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        paths: A dict mapping analysis files to their paths. Keys are strings
            and values may be strings or pathlib.Path objects. Must include the keys:

            * dem: The path to the DEM being analyzed
            * isburned: The path to the raster indicating which DEM pixels are burned.
                Burned pixels should have a value of 1. All other pixels should be 0.
            * flow_directions: The path for output D8 flow directions
            * total_area: The path for output total upslope area
            * burned_area: The path for output total burned upslope area
            * relief: The path for output vertical relief (of the longest flow path)

            The dict may optionally include the following two keys, which will
            cause the method to calculate debris-basin flow routing:

            * debris_basins: The path to the raster indicating which DEM pixels
                contain debris basins. Basin pixels should have a value of 1.
                All other pixels should be 0.
            * upslope_basins: The path for the output number of upslope debris basins

            The dict may optionally include any of the following keys for
            intermediate output files. If you provide one of these keys, the
            associated file will not be deleted. (Default behavior is to delete
            these files at the end of the function)

            * pitfilled: A path for the pitfilled DEM
            * flow_directions_dinf: A path for D-infinity flow directions
            * slopes_dinf: A path for D-infinity slopes

        outputs: Options are as follows
            "default": Return the paths of output files needed for standard hazard assessment
            "saved": Return the paths of all saved output files
            "all": Return the paths of all output files (including deleted
                intermediate outputs). Deleted files will have an value of None.
        verbose: Indicate how to treat TauDEM messages. If verbose=True, prints messages to
            the console. If verbose=False, suppresses the messages. If unspecified, uses
            the default verbosity setting for the module (initially set as False).

    Outputs:
        dict: A dict mapping output files to their absolute Paths. Always includes keys:

            * flow_directions: The path to the D8 flow directions
            * total_area: The path to the total upslope area
            * burned_area: The path to the total burned upslope area
            * relief: The path to the vertical relief of the longest flow path

            Will always include the following key if debris-basin flow routing
            was enabled:

            * upslope_basins

            May optionally include the following keys if outputs="saved".
            Will always include these keys if outputs="all". If using "all",
            files that were not saved will have a value of None.

            * pitfilled: The path to the pitfilled DEM
            * flow_directions_dinf: The path to the D-Infinity flow directions
            * slopes_dinf: The path to the D-Infinity slopes
    """

    # Parse verbosity and process file paths. Use temporary files when needed
    verbose = _verbosity(verbose)
    (paths, temporary, hasbasins) = _setup(paths)

    # Fill pits in the DEM
    try:
        pitremove(paths["dem"], paths["pitfilled"], verbose)

        # Compute D8 and D-infinity flow directions. (D8 is needed for upslope
        # areas, D-infinity for relief). Use user function for D8 to auto-delete
        # the flow slopes
        flow_directions(
            "D8", paths["pitfilled"], paths["flow_directions"], verbose=verbose
        )
        flow_dinf(
            paths["pitfilled"],
            paths["flow_directions_dinf"],
            paths["slopes_dinf"],
            verbose,
        )

        # Compute upslope area, burned upslope area, and optionally debris-basin
        # flow routing
        area_d8(paths["flow_directions"], None, paths["total_area"], verbose)
        area_d8(
            paths["flow_directions"], paths["isburned"], paths["burned_area"], verbose
        )
        if hasbasins:
            area_d8(
                paths["flow_directions"],
                paths["isbasin"],
                paths["upslope_basins"],
                verbose,
            )

        # Compute vertical relief of longest flow path
        relief_dinf(
            paths["pitfilled"],
            paths["flow_directions_dinf"],
            paths["slopes_dinf"],
            paths["relief"],
            verbose,
        )

    # Remove temporary output files
    finally:
        for name in temporary:
            paths[name].unlink(missing_ok=True)

    # Return dict of output file paths
    return _output_dict(paths, outputs, temporary, hasbasins)


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


def _verbosity(verbose: Union[bool, None]) -> bool:
    """
    _verbosity  Parses the verbosity setting for a function
    ----------
    _verbosity(verbose)
    Parses the "verbose" option for a function. The option is not altered if it
    is a bool. If the option is None (i.e. not set by the user), sets the option
    to the default value for the module. Returns a bool indicating the verbosity
    setting to use for the function.
    ----------
    Inputs:
        verbose (bool | None): The initial state of the verbose option

    Outputs:
        bool: The verbosity setting for the function.
    """

    if verbose is None:
        verbose = verbose_by_default
    return verbose


def _validate(
    verbose: Any, rasters: List[Any], names: Sequence[str]
) -> Tuple[bool, List[ValidatedRaster], bool]:
    """
    _validate  Validates verbosity and rasters for a routine
    ----------
    _validate(verbose, rasters, names)
    Validates and gets the verbosity setting. Validates rasters for a routine.
    The "rasters" input should be a list - the final element should be the output
    raster path (which may be None). All other elements should be input rasters.
    Returns the final verbosity setting, a list of validated rasters, and a bool
    indicating whether the output raster should be saved to file.
    ----------
    Inputs:
        verbose: The user-provided verbosity
        rasters: A list of user-provided rasters for the routine. The final element
            should be the output raster path. All other elements should be input
            rasters.
        names: A name for each raster for use in error messages.

    Outputs:
        3-tuple (bool, List[rasters], bool): First element is the verbosity
            setting. Second element is the list of validated rasters. Final element
            is whether the output raster should be saved to file.
    """
    verbose = _verbosity(verbose)
    input_indices = range(0, len(rasters) - 1)
    for r, raster, name in zip(input_indices, rasters, names):
        rasters[r] = validate.raster(raster, name, load=False)
    rasters[-1], save = _validate_output(rasters[-1])
    return verbose, rasters, save


def _paths(
    temp: TemporaryDirectory,
    rasters: List[ValidatedRaster],
    save: Sequence[OutputType],
    names: Sequence[str],
) -> List[Path]:
    """
    _paths  Returns file paths for the rasters needed for a routine
    ----------
    _paths(temp, rasters, output_type, names)
    Returns an file path for each provided raster. If the raster has no associated
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
            rasters[r] = write_raster(raster, tempfile)
        elif save == False:
            rasters[r] = tempfile
    return rasters


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
        save: True if returning a Path. False if returning a numpy 2D array.

    Outputs:
        pathlib.Path: The Path to the raster
        numpy 2D array: The raster data as a numpy array
    """
    if not save:
        raster = load_raster(raster)
    return raster


def _validate_output(path: Any) -> Tuple[Union[None, Path], bool]:
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
    ----------
    Inputs:
        path: The user-provided Path to an output raster.

    Outputs:
        (None|pathlib.Path, bool): A 2-tuple. First element is the Path for the
            output raster (which may be None). Second element indicates whether
            the output raster should be saved to file.
    """

    # Note whether saving to file
    if path is None:
        save = False
    else:
        save = True

        # If saving, get an absolute Path
        path = Path(path).resolve()

        # Ensure a .tif extension
        extension = path.suffix
        if extension.lower() in [".tiff", ".tif"]:
            path = path.with_suffix(".tif")
        else:
            name = path.name + ".tif"
            path = path.with_name(name)
    return path, save


#####
# Working
#####


def pitfill(
    dem: Raster, *, file: Optional[Pathlike] = None, verbose: Optional[bool] = None
) -> Output:
    """
    pitfill  Fills pits (depressions) in a DEM
    ----------
    pitfill(dem)
    Runs the TauDEM pitfilling routine on the input DEM. Returns the pitfilled
    DEM as a numpy 2D array.

    pitfill(..., *, file)
    Saves the pitfilled DEM to file. Returns the absolute Path to the saved file
    rather than a numpy array.

    pitfill(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        dem: The digital elevation model raster being pitfilled
        file: The path to a file in which to save the pitfilled DEM
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array: The pitfilled DEM
        pathlib.Path: The path to a saved pitfilled DEM

    Saves:
        Optionally saves the pitfilled DEM to a path matching the "file" input
    """

    names = ["dem","pitfilled"]
    verbose, [dem, pitfilled], save = _validate(verbose, [dem, file], names)
    with TemporaryDirectory() as temp:
        dem, pitfilled = _paths(temp, [dem, pitfilled], [None, save], names)
        pitremove(dem, pitfilled, verbose)
        return _output(pitfilled, save)


def flow_directions(
    type: Literal["D8", "DInf"],
    pitfilled: Raster,
    *,
    file: Optional[Pathlike] = None,
    return_slopes: Optional[bool] = False,
    slopes_file: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
) -> FlowOutput:
    """
    flow_directions  Computes D8 or D-Infinity flow directions and slopes
    ----------
    flow_directions(type, pitfilled)
    Computes D8 or D-Infinity flow directions from a pitfilled DEM. Returns the
    flow directions as a numpy 2D array. D8 flow directions are numbered from
    1 to 8 proceeding clockwise from right.

    flow_directions(..., *, file)
    Saves the flow directions to file. Returns the absolute Path to the raster
    file (rather than a numpy array).

    flow_directions(..., *, return_slopes)
    Also returns flow slopes. The output will be a 2-tuple - the first element is
    the flow-directions and the second element is the flow-slopes. The flow-slopes
    will be returned as a numpy 2D array.

    flow_directions(..., *, return_slopes=True, slopes_file)
    Saves flow slopes to file. Returns the absolute Path to the slopes file, rather
    than a numpy array. If return_slopes=False, then the slopes file is ignored.

    flow_directions(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        type: Use "D8" for a D8 flow model. Use "DInf" for a D-Infinity flow model.
        pitfilled: The pitfilled DEM from which flow directions will be computed
        file: A path at which to save computed flow directions
        return_slopes: True to also return flow slopes. False (default) to only
            return flow-directions.
        slopes_file: A path at which to save computed flow slopes. Ignored if
            return_slopes is False.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array | pathlib.Path: The flow directions or Path to the flow
            directions if not returning flow slopes.

        (flow_directions, flow_slopes): If also returning flow slopes, a 2-tuple
            whose first element is the flow directions and second element is the
            flow slopes. Each raster may either be a numpy 2D array, or a Path,
            depending on whether an output file was specified.

    Saves:
        Optionally saves flow-directions to a path matching the "file" input.
        Optionally saves flow slopes to a path matching the "slopes_file" input.
    """

    # Validate essential inputs. Optionally validate slopes
    names = ["pitfilled", "flow_directions", "slopes"]
    verbose, [pitfilled, flow], save = _validate(
        verbose, [pitfilled, file], names[0:-1]
    )
    if return_slopes:
        slopes, save_slopes = _validate_output(slopes_file)
    else:
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


def upslope_area(
    flow_directions: Raster,
    *,
    file: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
) -> Output:
    """
    upslope_area  Computes the upslope area (number of upslope pixels) over a DEM
    ----------
    upslope_area(flow_directions)
    Uses D8 flow directions to compute the upslope area (also known as contributing
    area) for a DEM. All pixels are given an area of 1, so this method effectively
    computes the number of pixels above a given point on the raster. Returns the
    upslope area as a numpy 2D array.

    upslope_area(..., *, file)
    Saves the upslope area to the designated file. Returns the Path to the raster,
    rather than a numpy 2D array.

    upslope_area(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        flow_directions: The raster of D8 flow directions used to compute upslope.
            Flow numbers should proceed from 1 to 8, clockwise from right.
        file: The path to a file in which to save the upslope area.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array: The upslope area raster as an array
        pathlib.Path: The Path to a saved upslope area raster

    Saves:
        Optionally saves upslope area to a path matching the "file" input.
    """

    names = ["flow_directions", "upslope area"]
    verbose, [flow, area], save = _validate(temp, [flow_directions, area], names)
    with TemporaryDirectory() as temp:
        flow, area = _paths(temp, [flow, area], [None, save], names)
        area_d8(flow, None, area, verbose)
        return _output(area, save)


def upslope_sum(
    flow_directions: Raster,
    weights: Raster,
    *,
    file: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
) -> Output:
    """
    upslope_sum  Computes the weighted sum of upslope pixels
    ----------
    upslope_sum(flow_directions, weights)
    Computes a weighted sum of upslope pixels. Each pixel is given a weight
    denoted by an associated weights raster. Returns the sum as a numpy 2D array.

    upslope_sum(..., *, file)
    Saves the upslope sum to the indicated file. Returns the Path to the saved
    upslope sum raster, rather than a numpy 2D array.

    upslope_sum(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        flow_directions: D8 flow directions used to determine upslope pixels. Flow
            numbers should proceed from 1 to 8, clockwise from right.
        weights: A weights raster, must have the same shape as the flow directions
            raster. Assigns a value to each pixel for the weighted sum.
        file: The path to a file in which to save the upslope sum.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array: The upslope sum raster.
        pathlib.Path: The Path to a saved upslope sum raster.

    Saves:
        Optionally saves the upslope sum raster to a path matching the "file" input.
    """

    names = ["flow_directions", "weights", "upslope sum"]
    verbose, [flow, weights, sum], save = _validate(
        temp, [flow_directions, weights, file], names
    )
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
    file: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
) -> Output:
    """
    relief  Computes the vertical relief along the longest flow path
    ----------
    relief(pitfilled, flow_directions, slopes)
    Computes the vertical relief along the longest flow path. Requires D-infinity
    flow directions and slopes. Returns the relief raster as a numpy 2D array.

    relief(..., *, file)
    Saves the relief raster to the indicated file. Returns the Path to the saved
    raster, rather than a numpy 2D array.

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
        file: The path to the file in which to save the vertical relief raster.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        numpy 2D array: The vertical relief raster.
        pathlib.Path: The Path to a saved vertical relief raster.

    Saves:
        Optionally saves the vertical relief to a path matching the "file" input.
    """

    names = ["pitfilled", "flow_directions", "slopes", "relief"]
    verbose, [pitfilled, flow, slopes, relief], save = _validate(
        verbose, [pitfilled, flow_directions, slopes, file], names
    )
    with TemporaryDirectory() as temp:
        pitfilled, flow, slopes, relief = _paths(
            temp, [pitfilled, flow, slopes, relief], [None, None, None, save], names
        )
        relief_dinf(pitfilled, flow, slopes, relief, verbose)
        return _output(relief, save)


#############################################################


def _output_dict(
    paths: PathDict, option: OutputOption, temporary: List[str], hasbasins: bool
) -> PathDict:
    """
    _output_dict  Returns the final dict of paths for a DEM analysis
    ----------
    _output_dict(paths, "default", temporary, hasbasins)
    Returns a dict with the paths of the D8 flow directions, total upslope area,
    total burned upslope area, and vertical relief. If hasbasins=True, also includes
    the path to the number of upslope debris basins

    _output_dict(paths, "saved", temporary, hasbasins)
    Returns a dict with the Paths of all saved output files.

    _output_dict(paths, "all", temporary, hasbasins)
    Returns a dict with the Paths of all output files possibly produced by the
    analysis. This includes temporary output files and the optional debris-basin
    output. Files that were not saved or produced have a value of None.
    ----------
    Inputs:
        paths: The dict of Paths for the analysis
        option: Indicates the keys that should be in the final dict. "default"
            includes all final output files. "saved" includes all saved output
            files. "all" includes all output files, but temporary files will have
            a value of None.
        temporary: The list of temporary files
        hasbasins: True if the analysis implemented debris-basin flow routing.
            Otherwise False.

    Outputs:
        Dict[str, Path]: A dict of output file Paths
    """

    # Determine the paths to include in the output
    if option == "default":
        include = _final.copy()
    else:
        outputs = _intermediate + _final
        include = [file for file in outputs if file not in temporary]

    # Optionally include the debris-basin output
    if hasbasins:
        include += [_basins[1]]

    # Add all paths to the dict. Optionally include temporary outputs as None
    output = {file: paths[file] for file in include}
    if option == "all":
        for file in temporary:
            output[file] = None
    return output


def _setup(paths: Dict[str, Pathlike]) -> Tuple[PathDict, List[str], bool]:
    """
    _setup  Prepares the path dict for a DEM analysis
    ----------
    _setup(paths)
    Processes user-provided paths. Gets temporary paths for intermediate files
    not specified by the user. Parses optional paths for debris basin flow
    routing. Returns a 3-tuple with (1) the dict of Paths, (2) the list of
    temporary output files, and (3) a bool indicating whether to enable debris
    basin flow routing.
    ----------
    Inputs:
        paths: The user-provided path dict

    Outputs:
        A 3-tuple with the following elements:

        Dict[str, Path]: A dict with the absolute Path for each file used in the
            analysis. May include temporary Paths for intermediate outputs.
        List[str]: The list of temporary output files.
        bool: True if flow-routing is enabled. Otherwise False.
    """

    # Initialize list of temporary files and get folder for temp files
    temporary = []
    paths["flow_directions"] = _output_path(paths["flow_directions"])
    folder = paths["flow_directions"].parent

    # Get file paths for basic analysis. Record temporary files
    outputs = _intermediate + _final
    core_files = _inputs + outputs
    for file in core_files:
        if file in _inputs:
            paths[file] = _input_path(paths[file])
        elif file in _final or (file in paths and paths[file] is not None):
            paths[file] = _output_path(paths[file])
        else:
            paths[file] = _temporary(file, folder)
            temporary += [file]

    # Optionally get paths for debris-basin flow routing
    [input, output] = _basins
    if input in paths and paths[input] is not None:
        paths[input] = _input_path(paths[input])
        paths[output] = _output_path(paths[output])
        hasbasins = True
    else:
        hasbasins = False

    # Return path dict, list of temporary files, and debris-basin switch
    return (paths, temporary, hasbasins)


