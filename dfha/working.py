"""
dem2 Updates the dem module with the new backend
"""

import numpy as np
from pathlib import Path
from tempfile import TemporaryDirectory
from dfha import validate, utils
from typing import Optional, Union, Tuple
from dfha.typing import Raster, RasterArray, Pathlike

# Type aliases
Output = Union[RasterArray, Path]
FlowSlopes = Tuple[Output, Output]
FlowOutput = Union[Output, FlowSlopes]


def pitfill(
    dem: Raster, 
    *, 
    file: Optional[Pathlike] = None, 
    verbose: Optional[bool] = None
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
    """

    verbose, [dem, pitfilled], asarray = _validate(verbose, [dem, pitfilled], ["dem","pitfilled"])
    with TemporaryDirectory() as temp:
        dem, pitfilled = _paths(temp, [dem,pitfilled], [None,asarray], ["dem","pitfilled"])
        pitremove(dem, pitfilled, verbose)
        return _output(pitfilled, asarray)
    

def upslope_area(
    flow_directions: Raster, 
    *, 
    file: Optional[Pathlike] = None,
    verbose: Optional[bool] = None
    ) -> Output:
    """
    upslope_area
    """

    verbose, [flow, area], asarray = _validate(temp, [flow_directions, area], ["flow_directions","area"])
    with TemporaryDirectory() as temp:
        flow, area = _paths(temp, [flow,area], [None,asarray], ["flow","area"])
        area_d8(flow, None, area, verbose)
        return _output(area, asarray)
    

def upslope_sum(
    flow_directions: Raster,
    weights: Raster,
    *,
    file: Optional[Pathlike] = None,
    verbose: Optional[Pathlike] = None,
) -> Output:
    
    verbose, [flow, weights, sum], asarray = _validate(temp, [flow_directions, weights, sum], ["flow_directions","weights","sum"])
    with TemporaryDirectory() as temp:
        flow, weights, area = _paths(temp, [flow,weights,area], [None,None,asarray], ["flow","weights","area"])
        area_d8(flow, weights, area, verbose)
        return _output(area, asarray)
    

def flow_directions(
    type: Literal["D8", "DInf"],
    pitfilled: Raster,
    *,
    file: Optional[Pathlike] = None,
    return_slopes: Optional[bool] = False,
    slopes_file: Optional[Pathlike] = None,
    verbose: Optional[bool] = None,
) -> FlowOutput:
    
    # Validate essential inputs. Optionally validate slopes
    verbose, [pitfilled, flow], asarray = _validate(verbose, [pitfilled, flow], ["pitfilled","flow"])
    if return_slopes:
        slopes, slopes_array = _parse_output(slopes_file)
    else:
        slopes_array = False

    # Get file paths, use temporary paths as necessary
    with TemporaryDirectory() as temp:
        pitfilled, flow, slopes = _paths(temp, [pitfilled,flow,slopes], output_type=[None,asarray,slopes_array], names=["pitfilled","flow_d8","slopes_d8"], temp)

        # Run the appropriate flow model
        if type=="D8":
            flow_model = flow_d8
        elif type=="DInf":
            flow_model = flow_dinf
        flow_model(pitfilled, flow, slopes, verbose)

        # ALways return flow. Optionally return slopes
        flow = _output(flow, asarray)
        if return_slopes:
            slopes = _output(slopes, slopes_array)
            return flow, slopes
        else:
            return flow


def _output(raster, asarray):
    if asarray:
        raster = utils.load_raster(raster)
    return raster

def _output_path(path, return_array, temp_path):
    if return_array:
        path = temp_path
    return path


def _parse_output(output_file):
    if output_file is None:
        return_array = True
    else:
        return_array = False

        output_file = _output_path(output_file)
    return output_file, return_array

    
def _paths(temp, rasters, output_type, names):
    temp = Path(temp)
    for r, raster, name, isinput in enumerate(zip(rasters, names, isinput)):
        temp_file = temp / (name+".tif")
        if output_type is None and not isinstance(raster, Path):
            rasters[r] = utils.write_raster(raster, temp_file)
        elif output_type == True:
            rasters[r] = temp_file
    return rasters

def _validate(verbose, rasters, isinput, names):
    verbose = _verbosity(verbose)
    for r, (raster, name, isinput) in enumerate(zip(rasters,names,isinput)):
        if isinput:
            rasters[r] = validate.raster(raster, name, load=False)
        elif raster is None:
            asarray = True
        else:
            asarray = False
            rasters[r] = _output_path(raster)
    return verbose, *rasters, asarray