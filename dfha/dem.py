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
interested in the "pitfill", "flow_directions", "upslope_area", and "relief"
functions, which implement individual pieces of this overall analysis.

In general, the functions in this module require various input rasters and
compute rasters as outputs. The module follows the raster file format
conventions of TauDEM: input rasters may use nearly any raster file format, but
outputs will always use a TIF format. For a complete list of supported input
raster formats, see:
https://gdal.org/drivers/raster/index.html

In addition to the user functions, this module includes the low-level 
"pitremove", "flow_d8", "flow_dinf", "area_d8", and "relief_dinf" functions, 
which provide wrappers to the TauDEM commands used to implement the analyses. 
These functions are primarily intended for developers, and we recommend that
most users instead use the aforementioned high-level functions.

The upslope areas output by this module are often used to help delineate a
stream network. As such, a suggested workflow for hazard assessment users is as
follows:
    * Acquire DEM data
    *** Run this module
    * Delineate a stream network
    * Filter the network to model-worthy drainages

REQUIREMENTS:
Running this module requires:
    * The ArcPy package and base Python environment shipped with ArcGIS Pro 3.0
      (Build Number 36056)
    * Installing TauDEM 5.3
----------
User functions:
    analyze             - Implements all DEM analyses required for standard hazard assessment
    pitfill             - Fills pits in a DEM
    flow_directions     - Computes D8 and D-Infinity flow directions and slopes
    upslope_area        - Computes contributing (upslope) area
    relief              - Computes the vertical component of the longest flow path

Low-level functions:
    pitremove          - Fills pits in a DEM
    flow_d8             - Computes D8 flow directions and slopes
    flow_dinf           - Computes D-infinity flow directions and slopes
    area_d8             - Computes D8 upslope area
    relief_dinf         - Computes vertical components of the longest flow path

Utilities:
    _verbosity          - Determines the verbosity setting for a routine
    _input_paths        - Returns absolute Paths for input files
    _output_path        - Returns the absolute Path for an output file
    _temporary          - Returns an absolute Path for a temporary file
    _run_taudem         - Runs a TauDEM routine as a subprocess
    _setup_dict         - Prepares the Path dict for a DEM analysis
    _output_dict        - Builds the output Path dict for a DEM analysis
"""

import subprocess, random, string
from pathlib import Path
from typing import Union, Optional, List, Literal, Tuple, Dict

# Configuration
verbose_by_default: bool = False  # Whether to print TauDEM messages to console
_tmp_string_length = 10  # The length of the random string for temporary files

# Names for files in a DEM analysis
_inputs = ["dem", "isburned"]
_intermediate = ["pitfilled", "flow_directions_dinf", "slopes_dinf"]
_final = ["flow_directions", "total_area", "burned_area", "relief"]

# Type aliases
Pathlike = Union[Path, str]
strs = Union[str, List[str]]
input_path = Union[Pathlike, None]
output_option = Literal["default", "saved", "all"]
pathdict = Dict[str, Path]


def analyze(
    paths: Dict[str, Pathlike],
    *,
    outputs: output_option = "default",
    verbose: Optional[bool] = None,
) -> pathdict:
    """
    analyze  Conducts all DEM analyses for a standard hazard assessment
    ----------
    analyze(paths)
    Conducts all DEM analyses required for a standard hazard assessment. Uses
    various routines from the TauDEM package. Begins by pitfilling a DEM and
    then computes flow directions and slopes. Uses the results of these initial
    analyses to compute total upslope area, total burned upslope area, and the
    vertical relief of the longest flow path. Returns a dict with the absolute
    Paths to the D8 flow directions, total upslope area, total burned upslope
    area, and vertical relief.

    The "paths" input is a dict mapping analysis files to their paths. It must
    contain the keys: 'dem', 'isburned', 'flow_directions', 'total_area',
    'burned_area', and 'relief'. (and see below for a description of these values)

    By default, the function will delete intermediate output files used in the
    analysis. These consist of the pitfilled DEM, and the D-infinity flow
    directions and slopes. You can save an intermediate file by including its
    key in the "paths" input, along with a path. The keys for these optional
    files are 'pitfilled', 'flow_directions_dinf', and 'slopes_dinf'. If you
    include one of these keys but its value is None, then the file will be
    deleted as usual.

    By default, the function will return a dict with the absolute Paths for the
    computed D8 flow directions, total upslope area, total burned upslope area,
    and vertical relief. (These are the computed DEM fields used for a standard
    hazard assessment). The keys for these outputs will match the corresponding
    keys in the "paths" input.

    analyze(..., *, outputs= "default" | "saved" | "all")
    Indicates the Paths that should be included in the output dict.
    If outputs="default", the dict includes the Paths of the D8 flow directions,
    total upslope area, total burned upslope area, and vertical relief.
    If outputs="saved", includes the keys for all saved output files. This includes
    the default 4 outputs, as well as any saved intermediate output files.
    If outputs="all", includes keys for all default and intermediate output files.
    If an intermediate output file was not saved, the value of its key will be None.

    analyze(..., *, verbose)
    Indicate how to treat TauDEM messages. If verbose=True, prints messages to
    the console. If verbose=False, suppresses the messages. If unspecified, uses
    the default verbosity setting for the module (initially set as False).
    ----------
    Inputs:
        paths: A dict mapping analysis files to their paths. Keys are strings
            and values may be strings or pathlib.Path objects. Must include the keys:

            * dem: The path to the DEM being analyzed
            * isburned: The path to the raster indicating which DEM pixels are burned
            * flow_directions: The path for output D8 flow directions
            * total_area: The path for output total upslope area
            * burned_area: The path for output total burned upslope area
            * relief: The path for output vertical relief (of the longest flow path)

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

            May optionally include the following keys if outputs="saved".
            Will always include these keys if outputs="all". If using "all",
            files that were not saved will have a value of None.

            * pitfilled: The path to the pitfilled DEM
            * flow_directions_dinf: The path to the D-Infinity flow directions
            * slopes_dinf: The path to the D-Infinity slopes
    """

    # Parse verbosity and process file paths. Use temporary files when needed
    verbose = _verbosity(verbose)
    (paths, temporary) = _setup_dict(paths)

    # Fill pits in the DEM
    try:
        pitremove(paths["dem"], paths["pitfilled"], verbose)

        # Compute D8 and D-infinity flow directions. (D8 is needed for upslope
        # areas, D-infinity for relief)
        flow_d8(paths["pitfilled"], paths["flow_d8"], None, verbose)
        flow_dinf(paths["pitfilled"], paths["flow_dinf"], paths["slopes_dinf"], verbose)

        # Compute upslope area and burned upslope area
        area_d8(paths["flow_d8"], None, paths["total_area"], verbose)
        area_d8(paths["flow_d8"], paths["isburned"], paths["burned_area"], verbose)

        # Compute vertical relief of longest flow path
        relief_dinf(
            paths["pitfilled"],
            paths["flow_dinf"],
            paths["slopes_dinf"],
            paths["relief"],
            verbose,
        )

    # Remove temporary output files
    finally:
        for name in temporary:
            paths[name].unlink(missing_ok=True)

    # Return dict of output file paths
    return _output_dict(paths, outputs, temporary)


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

    verbose = _verbosity(verbose)
    [pitfilled_path, flow_directions_path, slopes_path] = _input_paths(
        pitfilled_path, flow_directions_path, slopes_path
    )
    relief_path = _output_path(relief_path)
    relief_dinf(pitfilled_path, flow_directions_path, slopes_path, relief_path, verbose)
    return relief_path


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


def _input_paths(*files: input_path) -> List[input_path]:
    """
    _input_paths  Returns the absolute Paths to TauDEM input files
    ----------
    _input_paths(*files)
    Returns the absolute Paths to the indicated files as a list. If an input
    file is None, its value in the list will remain None. Raises a FileNotFoundError
    if the user provides a value for a file, but the file does not exist.
    ----------
    Inputs:
        *files: The user-provided paths to TauDEM input files. Files not provided
            by the user (i.e. optional inputs) should be None

    Outputs:
        List of pathlib.Path and None: The absolute Paths to the input files.
            Files that were None remain None in this list.

    Raises:
        FileNotFoundError: If the user provided a value for a file, but the file
            does not exist.
    """

    files = list(files)
    for f, file in enumerate(files):
        if file is not None:
            files[f] = Path(file).resolve(strict=True)
    return files


def _output_dict(
    paths: pathdict,
    option: Literal["default", "saved", "all"],
    temporary: List[str],
) -> pathdict:
    """
    _output_dict  Returns the final dict of paths for a DEM analysis
    ----------
    _output_dict(paths, "default", temporary)
    Returns a dict with the paths of the D8 flow directions, total upslope area,
    total burned upslope area, and vertical relief.

    _output_dict(paths, "saved", temporary)
    Returns a dict with the Paths of all saved output files.

    _output_dict(paths, "all", temporary)
    Returns a dict with the Paths of all output files. Output files that were
    not saved have a value of None.
    ----------
    Inputs:
        paths: The dict of Paths for the analysis
        option: Indicates the keys that should be in the final dict. "default"
            includes all final output files. "saved" includes all saved output
            files. "all" includes all output files, but temporary files will have
            a value of None.
        temporary: The list of temporary files

    Outputs:
        Dict[str, Path]: A dict of output file Paths
    """

    # Determine the paths to include in the output
    if option == "default":
        include = _final
    else:
        outputs = _intermediate + _final
        include = [file for file in outputs if file not in temporary]

    # Add all paths to the dict
    output = dict()
    for file in include:
        output[file] = paths[file]

    # Optionally include temporary outputs as None
    if option == "all":
        for file in temporary:
            output[file] = None

    return output


def _output_path(output: Pathlike) -> Path:
    """
    _output_path  Returns the path for an output file
    ----------
    _output_path(output)
    Returns an absolute Path for an output file produced by a TauDEM command.
    Ensures that the path ends with a ".tif" extension. If the input
    path ends with a case-insensitive .tif or .tiff, converts the extension to
    lowercase ".tif". Otherwise, appends ".tif" to the end of the path.
    ----------
    Inputs:
        output: A user-provided path for an output file

    Outputs:
        pathlib.Path: The absolute Path for the output file. Will always end
            with a .tif extension.
    """

    # Get an absolute path object
    output = Path(output).resolve()

    # Ensure a .tif extension
    extension = output.suffix
    if extension.lower() in [".tiff", ".tif"]:
        output = output.with_suffix(".tif")
    else:
        name = output.name + ".tif"
        output = output.with_name(name)
    return output


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


def _setup_dict(paths: Dict[str, Pathlike]) -> Tuple[pathdict, List[str]]:
    """
    _setup_dict  Prepares the path dict for a DEM analysis
    ----------
    _setup_dict(paths)
    Processes user-provided paths. Gets temporary paths for intermediate files
    not specified by the user. Returns a 2-tuple with the dict of Paths and the
    list of temporary output files.
    ----------
    Inputs:
        paths: The user-provided path dict

    Outputs:
        A 2-tuple with the following elements:

        Dict[str, Path]: A dict with the absolute Path for each file used in the
            analysis. May include temporary Paths for intermediate outputs.
        List[str]: The list of temporary output files.
    """

    # Initialize list of temporary files and get folder for temp files
    temporary = []
    paths["flow_directions"] = _input_paths(paths["flow_directions"])
    folder = paths["flow_directions"].parent

    # Get file paths
    all_files = _inputs + _intermediate + _final
    for file in all_files:
        if file in _inputs:
            paths[file] = _input_paths(paths[file])
        elif file in _final or (file in paths and paths[file] is not None):
            paths[file] = _output_path(paths[file])
        else:
            paths[file] = _temporary(file, folder)
            temporary += file

    # Return path dict and list of temporary files
    return (paths, temporary)


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
    tail = "".join(tail)
    name = f"{prefix}_{tail}.tif"
    return folder / name


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
