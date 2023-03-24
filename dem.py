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
    _verbosity           - Determines the verbosity setting for a routine
    _input_paths         - Returns absolute Paths for input files
    _output_path         - Returns the absolute Path for an output file
    _temporary           - Returns an absolute Path for a temporary file
    _run_taudem          - Runs a TauDEM routine as a subprocess
"""

import subprocess, random, string
from pathlib import Path
from typing import Union, Optional, List, Literal, Tuple, Dict

# Configuration
verbose_by_default: bool = False  # Whether to print TauDEM messages to console
_tmp_string_length = 10  # The length of the random string for temporary files

# Type aliases
Pathlike = Union[Path, str]
strs = Union[str, List[str]]
input_path = Union[Pathlike, None]


###
# High-level
###
def analyze(paths: Dict[str, Pathlike], *, verbose: Optional[bool] = None):

    # Fill pits
    pitfill(paths["dem"], paths["pitfilled"], verbose=verbose)

    # Compute both D8 and D-infinity flow directions. (D8 is required for
    # upslope areas, D-infinity is required for relief and length of longest
    # flow path)
    flow_directions(
        "D8", paths["pitfilled"], paths["flow_directions_D8"], verbose=verbose
    )
    flow_directions(
        "DInf",
        paths["pitfilled"],
        paths["flow_directions_DInf"],
        slopes=paths["slopes_DInf"],
        verbose=verbose,
    )

    # Get total area and total upslope burned area
    upslope_area(paths["flow_directions_d8"], paths["total_area"], verbose=verbose)
    upslope_area(paths["flow_directions_d8"], paths["burned_area"], verbose=verbose)

    # Get the relief and horizontal length of the longest flow path
    relief(
        paths["pitfilled"],
        paths["flow_directions_DInf"],
        paths["slopes_DInf"],
        paths["relief"],
        verbose=verbose,
    )
    length(
        paths["pitfilled"],
        paths["flow_directions_DInf"],
        paths["slopes_DInf"],
        paths["length"],
        verbose=verbose,
    )


def pitfill(
    dem_path: Pathlike,
    pitfilled_path: Pathlike,
    *,
    verbose: Optional[bool] = None,
) -> Path:
    """
    pitfill  Fills pits (depressions) in a DEM
    ----------
    pitfill(dem_path, pitfilled_path)
    Runs the TauDEM pitfilling routine on the input DEM. Saves the pitfilled
    DEM to the indicated path. Returns an absolute Path object to the output
    pitfilled DEM.

    pitfill(dem_path, pitfilled_path, *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        dem: The path to the input DEM being pitfilled
        pitfilled: The path to the output pitfilled DEM
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        pathlib.Path: The absolute Path to the output pitfilled DEM

    Saves:
        A file matching the "pitfilled" input.
    """

    verbose = _verbosity(verbose)
    [dem_path] = _input_paths(dem_path)
    pitfilled_path = _output_path(pitfilled_path)
    pitremove(dem_path, pitfilled_path, verbose)
    return pitfilled_path


def flow_directions(
    type: Literal["D8", "DInf"],
    pitfilled_path: Pathlike,
    flow_directions_path: Pathlike,
    *,
    slopes_path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
) -> Union[Path, Tuple[Path, Path]]:
    """
    flow_directions  Computes D8 or D-Infinity flow directions and slopes
    ----------
    flow_directions(type, pitfilled_path, flow_directions_path)
    Computes flow-directions from a pitfilled DEM. Uses a D8 or D-Infinity flow
    model, as indicated by the user. Saves the output flow directions to the
    indicated path and returns a Path object for the flow directions. (Note that
    this syntax deletes any output flow slopes produced by TauDEM).

    flow_directions(..., *, slopes_path)
    Also saves flow slopes to the indicated path. Returns a 2-tuple whose first
    element is the absolute Path for the flow directions, and whose second element
    is the absolute Path for the flow slopes.

    flow_directions(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        type: The type of flow model to use. Set as "D8" for a
            D8 flow model. Set to "DInf" for a D-infinity flow model.
        pitfilled_path: The path to the input pitfilled DEM
        flow_directions_path: The path for the output flow directions
        slopes_path: The optional path for output flow slopes. If not specified,
            output flow slopes will be deleted.
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        pathlib.Path: If no flow slope path is provided, returns the path to the
            output flow directions

        tuple(pathlib.Path, pathlib.Path): If a flow slope path is provided,
            returns a tuple whose first element is the path to the flow directions,
            and whose second element is the path to the flow slopes.

    Saves.
        A file matching the "flow_directions" path. Optionally also saves a file
        matchinge the "slopes" path.
    """

    # Parse options and paths
    verbose = _verbosity(verbose)
    [pitfilled_path] = _input_paths(pitfilled_path)
    flow_directions_path = _output_path(flow_directions_path)

    # Optional slopes path. Only save slopes if provided by user. Otherwise, use
    # a temporary file
    if slopes_path is None:
        slopes_path = _temporary("slopes", flow_directions_path.parent())
        delete_slopes = True
    else:
        slopes_path = _output_path(slopes_path)
        delete_slopes = False

    # Get function for indicated flow type
    if type == "D8":
        flow = flow_d8
    elif type == "DInf":
        flow = flow_dinf

    # Run. Delete slopes if using a temp file
    try:
        flow(pitfilled_path, flow_directions_path, slopes_path, verbose)
    finally:
        if delete_slopes:
            slopes_path.unlink(missing_ok=True)

    # Return flow-directions and optionally slopes
    if delete_slopes:
        return flow_directions_path
    else:
        return (flow_directions_path, slopes_path)


def upslope_area(
    flow_directions_path: Pathlike,
    area_path: Pathlike,
    *,
    weights_path: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
) -> Path:
    """
    upslope_area  Computes upslope area
    ----------
    upslope_area(flow_directions_path, area_path)
    Computes upslope area (also known as contributing area) using flow directions
    from a D8 flow model. Gives all DEM pixels an equal area of 1. Saves the
    output upslope area to the indicated path.

    upslope_area(..., *, weights_path)
    Computes weighted upslope area. The area of each DEM pixel is set as the
    value of the corresponding pixel in the weight raster.

    upslope_area(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        flow_directions_path: The path to the input D8 flow directions used to
            compute upslope area
        area_path: The path to the output upslope area.
        weights_path: The optional path to an area weights raster
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        pathlib.Path: The absolute Path to the output usplope areas

    Saves:
        A file matching the "area" path
    """

    verbose = _verbosity(verbose)
    [flow_directions_path, weights_path] = _input_paths(
        flow_directions_path, weights_path
    )
    area_path = _output_path(area_path)
    area_d8(flow_directions_path, weights_path, area_path, verbose)
    return area_path


def relief(
    pitfilled_path: Pathlike,
    flow_directions_path: Pathlike,
    slopes_path: Pathlike,
    relief_path: Pathlike,
    *,
    verbose: Optional[bool] = None,
) -> Path:
    """
    relief  Computes the vertical relief of the longest flow path
    ----------
    relief(pitfilled_path, flow_directions_path, slopes_path, relief_path)
    Computes the vertical relief of the longest flow path using a pitfilled DEM,
    and D-infinity flow directions and slopes. Saves the output relief to the
    indicated path.

    relief(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        pitfilled_path: The path to the input pitfilled DEM
        flow_directions_path: The path to the input D-infinity flow directions
        slopes_path: The path to the input D-infinity slopes
        relief_path: The path to the output vertical relief
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        pathlib.Path: The absolute Path to the output vertical relief
    """

    return _compute_longest(
        "vertical",
        pitfilled_path,
        flow_directions_path,
        slopes_path,
        relief_path,
        verbose,
    )


def length(
    pitfilled_path: Pathlike,
    flow_directions_path: Pathlike,
    slopes_path: Pathlike,
    length_path: Pathlike,
    *,
    verbose: Optional[bool] = None,
) -> Path:
    """
    length  Computes the horizontal length of the longest flow path
    ----------
    length(pitfilled_path, flow_directions_path, slopes_path, length_path)
    Computes the horizontal length of the longest flow path using a pitfilled DEM,
    and D-infinity flow directions and slopes. Saves the output length to the
    indicated path.

    length(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        pitfilled_path: The path to the input pitfilled DEM
        flow_directions_path: The path to the input D-infinity flow directions
        slopes_path: The path to the input D-infinity slopes
        length_path: The path to the output horizontal length
        verbose: Set to True to print TauDEM messages to the console. False to
            suppress these messages. If unset, uses the default verbosity for
            the module (initially set as False).

    Outputs:
        pathlib.Path: The absolute Path to the output vertical relief
    """

    return _compute_longest(
        "horizontal",
        pitfilled_path,
        flow_directions_path,
        slopes_path,
        length_path,
        verbose,
    )


#####
# LOW LEVEL
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

    area_d8 = f"AreaD8 -p {flow_directions_path} -ad8 {area_path}"
    if weights_path is not None:
        area_d8 += f" -wg {weights_path}"
    _run_taudem(area_d8, verbose)


def longest(
    direction: Literal["horizontal", "vertical"],
    pitfilled_path: Path,
    flow_directions_path: Path,
    slopes_path: Path,
    length_path: Path,
    verbose: bool,
) -> None:
    """
    longest  Computes the horizontal or vertical component of the longest flow path
    ----------
    longest(direction, pitfilled_path, flow_directions_path, slopes_path,
            length_path, verbose)
    Computes the horizontal or vertical component of the longest flow path. This
    analysis requires an input pitfilled DEM, and D-Infinity flow directions and
    slopes. The routine is set to account for edge contamination. Uses a
    threshold of 0.49 so that computed lengths mimic the results for a D8 flow
    model. Saves the computed length to the indicated path. Optionally prints
    TauDEM messages to the console.
    ----------
    Inputs:
        direction ('horiztonal | 'vertical'): Indicates whether the method should
            compute the horizontal or vertical component of the longest flow path.
        pitfilled_path: The absolute Path to the input pitfilled DEM
        flow_directions_path: The absolute Path to the input D-infinity flow directions
        slopes_path: The absolute Path to the input D-infinity slopes
        length_path: The absolute Path to the output D8 lengths
        verbose (bool): True to print TauDEM messages to the console. False to
            suppress these messages.

    Outputs: None

    Saves:
        A file matching the "length" path.
    """

    # Get the key for vertical/horizontal
    if direction == "vertical":
        direction = "v"
    else:
        direction = "h"

    # Run the command. The "thresh 0.49" option mimics results for a D8 flow model. The
    # "nc" flag causes the routine to account for edge contamination.
    # The "-m max" computes values for the longest flow path. The "h" and "v"
    # direction keys indicate the horiztonal or vertical component of the length
    length = (
        f"DinfDistUp -fel {pitfilled_path} -ang {flow_directions_path} -slp {slopes_path}"
        + f" -du {length_path} -m max {direction} -thresh 0.49 -nc"
    )
    _run_taudem(length, verbose)


###
# Utilities
###
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


def _input_paths(*files: input_path) -> List[input_path]:
    """
    _input_paths  Returns the absolute Paths to TauDEM input files
    ----------
    _input_paths(*files)
    Returns the absolute Paths to the indicated files as a list. If an input
    file is None, its value in the list will remain None.
    ----------
    Inputs:
        *files: The user-provided paths to TauDEM input files. Files not provided
            by the user (i.e. optional inputs) should be None

    Outputs:
        List of pathlib.Path and None: The absolute Paths to the input files.
            Files that were None remain None in this list.
    """

    files = list(files)
    for f, file in enumerate(files):
        if file is not None:
            files[f] = Path(file).absolute()
    return files


def _output_path(output: Pathlike) -> Path:
    """
    _output_path  Returns the path for an output file
    ----------
    _output_path(output)
    Returns an absolute Path for an output file produced by a TauDEM command.
    Ensures that the path ends with a ".tif" extension. If the input
    path ends with a case-insensitive .tif or .tiff, converts the extension to
    lowercase ".tif". Otherwise, append, ".tif" to the end of the path.
    ----------
    Inputs:
        output (str | Path): A user-provided path for an output file

    Outputs:
        pathlib.Path: The absolute Path for the output file. Will always end
            with a .tif extension.
    """

    # Get an absolute path object
    output = Path(output).absolute()

    # Ensure a .tif extension
    extension = output.suffix()
    if extension.lower() in [".tiff", ".tif"]:
        output = output.with_suffix(".tif")
    else:
        name = output.name() + ".tif"
        output = output.with_name(name)


def _temporary(prefix: str, folder: Path) -> Path:
    """
    _temporary  Returns a path for a temporary file
    ----------
    _temporary(prefix, folder)
    Returns an absolute Path for a temporary file. The file name will follow the
    format <prefix>_<random ASCII letters>.tif. Places the file in the indicated
    folder.
    ----------
    Inputs:
        prefix: A prefix for the file name
        folder: The folder that should contain the temporary file

    Outputs:
        pathlib.Path: The absolute Path for the temporary file.
    """

    tail = random.choices(string.ascii_letters, k=_tmp_string_length)
    name = f"{prefix}_{tail}.tif"
    return folder / name


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

    subprocess.run(command, capture_output=not verbose, check=True)


def _compute_longest(
    direction: Literal["vertical", "horizontal"],
    pitfilled_path: Pathlike,
    flow_directions_path: Pathlike,
    slopes_path: Pathlike,
    length_path: Pathlike,
    verbose: Union[bool, None],
):
    """
    _compute_longest  Parses user inputs and implements a longest flow path routine
    ----------
    _compute_longest(direction, pitfilled_path, flow_directions_path, slopes_path
                     length_path, verbose)
    Parses the verbosity setting and processes user provided file paths prior to
    computing a component of the longest flow path. Computes either the
    horizontal or vertical component of the longest flow path, as specified.
    ----------
    Inputs:
        direction: Indicates whether to compute the vertical or horizontal
            component of the longest flow path
        pitfilled_path: The user provided path to the pitfilled DEM
        flow_directions_path: The user provided path to the D-infinity flow directions
        slopes_path: The user provided path to the D-infinity flow slopes
        length_path: The user provided path to the output length
        verbose: The user provided verbosity setting

    Outputs:
        pathlib.Path: The path to the output length

    Saves:
        A file matching the "length" path
    """

    verbose = _verbosity(verbose)
    [pitfilled_path, flow_directions_path, slopes_path] = _input_paths(
        pitfilled_path, flow_directions_path, slopes_path
    )
    length_path = _output_path(length_path)
    longest(
        direction,
        pitfilled_path,
        flow_directions_path,
        slopes_path,
        length_path,
        verbose,
    )
    return length_path
