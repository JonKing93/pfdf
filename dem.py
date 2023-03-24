"""
dem  Functions that implement DEM analysis
----------
The dem module provide functions that implement basic analyses on a Digital
Elevation Model (DEM). These include pitfilling, analysis of flow directions, 
and the calculation of upslope areas.

Currently, this module relies on the command-line tools of the TauDEM package.
Documentation of TauDEM is available here:
https://hydrology.usu.edu/taudem/taudem5/documentation.html

Many of the outputs of this module are required to delineate a stream network.
A suggested workflow for hazard assessment users is as follows:
    * Acquire DEM data
    *** Run this module
    * Delineate a stream network
    * Filter the network to model-worthy drainages

REQUIREMENTS:
Running this module requires:
    * The ArcPy package and base Python environment shipped with ArcGIS Pro 3.0
      (Build Number 36056)
----------
User functions:
    analyze             - Implements all DEM analyses required for hazard assessment
    pitfill             - Fills pits in a DEM
    flow_directions     - Computes D8 and D-Infinity flow directions and slopes
    upslope_area        - Computes contributing (upslope) area
    relief              - Computes the vertical component of the longest flow path
    length              - Computes the horizontal component of the longest flow path

Low-level functions:
    pit_remove          - Fills pits in a DEM
    flow_d8             - Computes D8 flow directions and slopes
    flow_di             - Computes D-infinity flow directions and slopes
    area                - Computes D8 upslope area
    longest             - Computes vertical and horizontal components of the longest flow path

Utilities:
    _parse_options       - Determines the verbosity setting for a routine
    _input_paths         - Returns absolute Paths for input files
    _output_path         - Returns the absolute Path for an output file
    _compute_longest     - Processes inputs and analyzes the longest flow path
    _run_taudem          - Runs a TauDEM routine as a subprocess
"""

import subprocess, random, string
from pathlib import Path
from typing import Union, Optional, List, Literal, Tuple, Dict

# Configuration 
verbose_by_default: bool = False  # Whether to print TauDEM messages to console
_tmp_string_length = 10 

# Type aliases
Pathlike = Union[Path, str]
strs = Union[str, List[str]]


###
# High-level
###
def analyze(paths: Dict[str, Pathlike], *, verbose: Optional[bool]=None):

    # Fill pits
    pitfill(paths['dem'], paths['pitfilled'], verbose=verbose)

    # Compute both D8 and D-infinity flow directions. (D8 is required for
    # upslope areas, D-infinity is required for relief and length of longest
    # flow path)
    flow_directions('D8', paths['pitfilled'], paths['flow_directions_D8'], verbose=verbose)
    flow_directions('DInf', paths['pitfilled'], paths['flow_directions_DInf'],
                    slopes = paths['slopes_DInf'], verbose = verbose)
    
    # Get total area and total upslope burned area
    upslope_area(paths['flow_directions_d8'], paths['total_area'], verbose=verbose)
    upslope_area(paths['flow_directions_d8'], paths['burned_area'], verbose=verbose)

    # Get the relief and horizontal length of the longest flow path
    relief(paths['pitfilled'], paths['flow_directions_DInf'], paths['slopes_DInf'],
           paths['relief'], verbose=verbose)
    length(paths['pitfilled'], paths['flow_directions_DInf'], paths['slopes_DInf'],
           paths['length'], verbose=verbose)


def pitfill(
    dem: Pathlike,
    pitfilled: Pathlike,
    *,
    verbose: Optional[bool] = None,
) -> Path:
    """
    pitfill  Fills pits (depressions) in a DEM
    ----------
    pitfill(dem, pitfilled)
    Runs the TauDEM pitfilling routine on the input DEM. Saves the pitfilled
    DEM to the indicated path. Returns a Path object for the output pitfilled DEM.

    pitfill(dem, pitfilled, *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to 
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        dem (str | pathlib.Path): The path to the input DEM being pitfilled
        pitfilled (str | pathlib.Path): The path to the output pitfilled DEM
        verbose (Optional bool): Set as true to print TauDEM messages to the
            console. False to suppress these messages. If unset, uses the default
            verbosity for the module

    Outputs:
        pathlib.Path: The absolute Path to the output pitfilled DEM

    Saves:
        A file matching the "pitfilled" input.
    """
    
    verbose = parse_options(verbose)
    [dem] = input_paths(dem)
    pitfilled = output_path(pitfilled)
    pitremove(dem, pitfilled, verbose)
    return pitfilled


def flow_directions(
        type: Literal["D8","DInf"], 
        pitfilled: Pathlike, 
        flow_directions: Pathlike, 
        *, 
        slopes: Optional[Pathlike] = None, 
        verbose: Optional[bool] = None,
        ) -> Union[Path, Tuple[Path, Path]]:
    """
    flow_directions  Computes D8 and D-Infinity flow directions and slopes
    ----------
    flow_directions(type, pitfilled, flow_directions)
    Computes flow-directions from a pitfilled DEM. Uses a D8 or D-Infinity flow
    model, as indicated by the user. Saves the output flow directions to the
    indicated path and returns a Path object for the flow directions.

    flow_directions(..., *, slopes)
    Also saves flow slopes to the indicated path. Returns a 2-tuple whose first
    element is a Path object for the flow directions, and whose second element
    is a Path object for the flow slopes.

    flow_directions(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to 
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        type ("D8" | "DInf"): The type of flow model to use. Set as "D8" for a 
            D8 flow model. Set to "DInf" for a D-infinity flow model.
        pitfilled (str | pathlib.Path): The path to the input pitfilled DEM
        flow_directions (str | pathlib.Path): The path to use for the output 
            flow directions
        slopes (str | pathlib.Path): Optionally used to indicate the
            path to the output flow slopes. If not specified, output flow slopes
            will be deleted.
        verbose (optional bool): True to print TauDEM messages to the console. 
            False to suppress these messages. If unset, uses the default
            verbosity for the module.

    Outputs:
        pathlib.Path: If no flow slopes are provided, returns the path to the
            output flow directions
        tuple(pathlib.Path, pathlib.Path): If flow slopes are saved, returns a 
            tuple whose first element is the path to the flow directions, and
            whose second element is the path to the flow slopes.

    Saves.
        A file matching the "flow_directions" input. Optionally also saves a file
        matchinge the "slopes" input.
    """

    # Parse options and paths
    verbose = parse_options(verbose)
    [pitfilled] = input_paths(pitfilled)
    flow_directions = output_path(flow_directions)

    # Optional slopes path. Only save slopes if provided by user. Otherwise, use
    # a temporary file
    if slopes is None:
        slopes = temporary("slopes", flow_directions.parent())
        return_slopes = False
    else:
        slopes = output_path(slopes)
        return_slopes = True

    # Get function for indicated flow type
    if type == "D8":
        flow = flow_d8
    elif type == "DInf":
        flow = flow_dinf

    # Run. Delete slopes if using a temp file
    try:
        flow(pitfilled, flow_directions, slopes, bool)
    finally:
        if not return_slopes:
            slopes.unlink(missing_ok = True)

    # Return flow-directions and optionally slopes
    if return_slopes:
        return (flow_directions, slopes)
    else:
        return flow_directions


def upslope_area(
        flow_directions: Pathlike, 
        area: Pathlike, 
        *, 
        weights: Optional[Pathlike] = None,
        verbose: Optional[bool] = None,
        ) -> Path:
    """
    upslope_area  R
    """
    verbose = parse_options(verbose)
    [flow_directions, weights] = input_paths(flow_directions, weights)
    area = output_path(area)
    area_d8(flow_directions, weights, area, verbose)
    return area


def relief(pitfilled, flow_directions, slopes, relief, *, verbose):

    compute_longest("vertical", pitfilled, flow_directions, slopes, relief, verbose)


def length(pitfilled, flow_directions, slopes, length, *, verbose):

    compute_longest("horizontal", pitfilled, flow_directions, slopes, length, verbose)


#####
# LOW LEVEL
#####
def pitremove(dem: Path, pitfilled: Path, verbose: bool) -> None:
    """
    pitremove  Runs the TauDEM PitRemove routine
    ----------
    pitremove(dem, pitfilled, verbose)
    Runs the TauDEM pit filling routine on a input DEM. Saves the output
    pitfilled DEM to the indicated path. Optionally prints TauDEM messages to
    the console.
    ----------
    Inputs:
        dem (pathlib.Path): The absolute Path object for the input DEM
        pitfilled (pathlib.Path): The absolute Path object for the output
            pitfilled DEM.
        verbose (bool): True if TauDEM messages should be printed to the console.
            False if the messages should be suppressed.

    Outputs: None

    Saves: A file matching the path indicated by the "pitfilled" input
    """

    pitremove = f"PitRemove -z {dem} -fel {pitfilled}"
    run_taudem(pitremove, verbose)


def flow_d8(
    pitfilled: Path, flow_directions: Path, slopes: Path, verbose: bool
) -> None:
    """
    flow_d8  Runs the TauDEM D8 flow direction routine
    ----------
    flow_d8(pitfilled, flow_directions, slopes, verbose)
    Calculates flow directions and slopes from a pitfilled DEM using a D8 flow
    model. Saves the output flow directions and slopes to the indicated paths.
    Optionally prints TauDEM messages to the console.
    ----------
    Inputs:
        pitfilled (pathlib.Path): The absolute Path to the pitfilled DEM being
            analyzed.
        flow_directions (pathlib.Path): The absolute Path for the output flow
            directions
        slopes (pathlib.Path): The absolute Path for the output slopes
        verbose (bool): True if TauDEM messages should be printed to console.
            False if these messages should be suppressed.

    Outputs: None

    Saves:
        Files matching the "flow_directions" and "slopes" paths.
    """

    flow_d8 = f"D8FlowDir -fel {pitfilled} -p {flow_directions} -sd8 {slopes}"
    run_taudem(flow_d8, verbose)


def flow_dinf(
    pitfilled: Path, flow_directions: Path, slopes: Path, verbose: bool
) -> None:
    """
    flow_dinf  Runs the TauDEM D-Infinity flow direction routine
    ----------
    flow_dinf(pitfilled, flow_directions, slopes, verbose)
    Calculates flow directions and slopes from a pitfilled DEM using a
    D-infinity flow model. Saves the output flow directions and slopes to the
    indicated paths. Optionally prints TauDEM messages to the console.
    ----------
    Inputs:
        pitfilled (pathlib.Path): The absolute Path to the pitfilled DEM being
            analyzed.
        flow_directions (pathlib.Path): The absolute Path for the output flow
            directions
        slopes (pathlib.Path): The absolute Path for the output slopes
        verbose (bool): True if TauDEM messages should be printed to console.
            False if these messages should be suppressed.

    Outputs: None

    Saves:
        Files matching the "flow_directions" and "slopes" paths.
    """

    flow_dinf = f"DInfFlowDir -fel {pitfilled} -ang {flow_directions} -slp {slopes}"
    run_taudem(flow_dinf, verbose)


def area_d8(
    flow_directions: Path, weights: Union[Path, None], area: Path, verbose: bool
) -> None:
    """
    area_d8  Runs the TauDEM D8 upslope area routine
    ----------
    area_d8(flow_directions, weights=None, area, verbose)
    Computes upslope area using a D8 flow model. All raster pixels are given
    an equal area of 1. Saves the output upslope area to the indicated path.
    Optionally prints TauDEM messages to the console.

    area_d8(flow_directions, weights, area, verbose)
    Computes weighted upslope area. The area of each raster pixel is set to the
    corresponding value in the weights raster.
    ----------
    Inputs:
        flow_directions (pathlib.Path): The absolute Path for the input D8 flow
            directions.
        weights (Path | None): The absolute Path to the input raster holding
            area weights for each pixel. If None, computes unweighted upslope area.
        area (pathlib.Path): The absolute Path to the output upslope area
        verbose (bool): True if TauDEM messages should be printed to the console.
            False to suppress these messages.

    Outputs: None

    Saves:
        A file matching the "area" input.
    """

    area_d8 = f"AreaD8 -p {flow_directions} -ad8 {area}"
    if weights is not None:
        area_d8 += f" -wg {weights}"
    run_taudem(area_d8, verbose)


def longest(
    direction: Literal["horizontal", "vertical"],
    pitfilled: Path,
    flow_directions: Path,
    slopes: Path,
    length: Path,
    verbose: bool,
) -> None:
    """
    longest  Computes the horizontal or vertical component of the longest flow path
    ----------
    longest(direction, pitfilled, flow_directions, slopes, length, verbose)
    Computes the horizontal or vertical component of the longest flow path. This
    analysis requires an input pitfilled DEM, and D-Infinity flow directions and
    slopes. The routine is set to account for edge contamination. Uses a
    threshold of 0.49 so that computed lengths mimic the results for a D8 flow
    model. Saves the computed length to the indicated file. Optionally prints
    TauDEM messages to the console.
    ----------
    Inputs:
        direction ('horiztonal | 'vertical'): Indicates whether the method should
            compute the horizontal or vertical component of the longest flow path.
        pitfilled (pathlib.Path): The absolute Path to the input pitfilled DEM
        flow_directions (pathlib.Path): The absolute Path to the input
            D-infinity flow directions
        slopes (pathlib.Path): The absolute Path to the input D-infinity slopes
        length (pathlib.Path): The absolute Path to the output D8 lengths
        verbose (bool): True to print TauDEM messages to the console. False to
            suppress these messages.

    Outputs: None

    Saves:
        A file matching the input "length" path.
    """

    # Get the key for vertical/horizontal
    if direction == "vertical":
        direction = "v"
    else:
        direction = "h"

    # Run the command. The thresh option mimics results for a D8 flow model. The
    # "nc" flag causes the routine to account for edge contamination.
    # The "-m max" computes values for the longest flow path. The "h" and "v"
    # direction keys indicate the horiztonal or vertical component of the length
    length = (
        f"DinfDistUp -fel {pitfilled} -ang {flow_directions} -slp {slopes}"
        + f" -du {length} -m max {direction} -thresh 0.49 -nc"
    )
    run_taudem(length, verbose)


#####
# UTILITIES
#####
def parse_options(overwrite: option, verbose: option):
    """
    parse_options  Parses the overwrite and verbose options
    ----------
    parse_options(overwrite, verbose)
    Parses the overwrite and verbose options for a function. The option is not
    altered if it is a bool. If the option is None, sets the option to the
    default value for the module. Returns a 2-tuple whose first element is the
    value for the overwrite option, and whose second element is the value for
    the verbose option.
    ----------
    Inputs:
        overwrite (bool | None): The initial state of the overwrite option
        verbose (bool | None): The initial state of the verbose option

    Outputs:
        A 2-tuple. The first element is the setting for the overwrite option,
        and the second element is the setting for the verbose option.
    """

    if overwrite is None:
        overwrite = overwrite_by_default
    if verbose is None:
        verbose = verbose_by_default
    return (overwrite, verbose)


def input_paths(*files):
    files = list(files)
    for f, file in enumerate(files):
        if file is not None:
            files[f] = Path(file).absolute()
    return files


def temporary(name, folder):

    tail = random.choices(string.ascii_letters, k=_tmp_string_length)
    name = name + "_" + tail + ".tif"
    return folder / name


def output_path(output):
    """
    output_path  Returns the path for an output file
    ----------
    output_path(output)
    Returns an absolute Path object for an output file for use with a TauDEM
    command. Ensures that the path ends with a ".tif" extension. If the input
    path ended with .tiff, .TIF, or .TIFF, converts the extension to ".tif".
    Otherwise, appends ".tif" to the end of the path. The returned path will be
    for a temporary file - the tmp file is derived by appending a sequence of 
    random ascii letter to end of the file stem. (See also the "finalize"
    function for moving a tmp file to the user specified path).
    ----------
    Inputs:
        output (str | Path): A user-provided path for an output file

    Outputs:
        pathlib.Path: The absolute Path to the temporary output file. Will
            always end with a .tif extension.
    """

    # Get an absolute path object
    output = Path(output).absolute()

    # Ensure a .tif extension
    extension = output.suffix()
    if extension in [".tiff",".TIF",".TIFF"]:
        output = output.with_suffix(".tif")
    else:
        name = output.name() + ".tif"
        output = output.with_name(name)

    # Use a temporary file.
    tail = random.choices(string.ascii_letters, k=_tmp_string_length)
    stem = output.stem() + tail
    output = output.with_stem(stem)


def compute_longest(direction, pitfilled, flow_directions, slopes, length, verbose):

    verbose = parse_options(verbose)
    [pitfilled, flow_directions, slopes] = input_paths(pitfilled, flow_directions, slopes)
    length = output_path(length)
    longest("horiztonal", pitfilled, flow_directions, slopes, length, verbose)


def run_taudem(command: strs, verbose: bool) -> None:
    """
    run_taudem  Runs a TauDEM command as a subprocess
    ----------
    run_taudem(command, verbose)
    Runs a TauDEM command as a subprocess. If verbose=True, prints TauDEM
    messages to the console. If verbose=False, suppresses these messages. Raises
    a CalledProcessError if the TauDEM process does not complete successfully
    (i.e. the process returns an exit code not equal to 0).
    ----------
    Inputs:
        command: The arguments used to run a TauDEM command
        verbose: True if TauDEM messages should be printed to the
            console. False if these messages should be suppressed.

    Outputs: None

    Saves:
        Whatever output files are produced by the given TauDEM command.

    Raises:
        CalledProcessError: If the TauDEM process returns an exit code not
            equal to 0.
    """

    try:
        subprocess.run(command, capture_output=not verbose, check=True)


