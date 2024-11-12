"""
Functions to build a basin raster in parallel
----------
This module contains functions used to efficiently build a basin raster. Building
a basin raster is an expensive CPU-bound operation, so the module uses the
multiprocessing library to parallelize this operation via a process Pool when
appropriate. Multiprocessing imposes several restrictions on user code, so the
user must explicitly request parallelization before a process pool will be 
activated. When multiprocess is not requested, or not possible (i.e. only 1
available CPU), the module builds the basin raster sequentially.

For the sake of parallelization, it is useful to distinguish between raster
*groups* and *chunks*. A group is a set of basins for which each raster has 
the same number of terminal outlets flowing into it. As such, it is impossible
for the basins in a group to flow into one another, and so the basins in a group
may be processed in parallel. The groups themselves are processed sequentially.
The first processed groups have priority over later groups, so groups should be
processed from downstream to upstream to ensure that shared pixels are assigned
to downstream basins.

By contrast, a chunk is a set of basins that are processed sequentially. When
running in parallel, each group is split into a number of chunks equal to the
number of parallel processes. This ensures that the number of parallel basin
rasters matches the number of processes, rather than the (potentially very large)
number of terminal basins. When the basin raster is not built in parallel, 
the operation processes all the basins as a single chunk. In this context, it is 
important to note that the final processed basins have priority over the initial 
basins, so basins should be processed from upstream to downstream (the opposite 
order as groups) to ensure that shared pixels are assigned to downstream basins.

Each process in the parallel pool is initialized with a flow direction raster.
This reduces communication overhead when reusing the pool for multiple groups.
We pass pfdf.raster.Raster objects, rather than pysheds rasters, because pysheds
objects do not appear to initialize correctly in parallel Processes (a limitation 
that may relate to picklability).
----------
Raster builders:
    build              - Builds a basin raster sequentially or in parallel, as appropriate
    built_sequentially - Builds a basin raster sequentially
    built_in_parallel  - Builds a basin raster in parallel
    group_rasters      - Builds the rasters for a basin group in parallel
    chunk_raster       - Builds the raster for a set of ordered basins sequentially

Utilities:
    get_outlets        - Returns the IDs and locations of terminal outlets
    count_outlets      - Counts the number of terminal outlets flowing into each basin
    initializer        - Initializes a parallel Process with flow directions
    update_raster      - Updates the final basin raster using the rasters from a group
"""

from __future__ import annotations

import typing
from multiprocessing import Pool

import numpy as np
from pysheds.grid import Grid

import pfdf.segments._validate as validate
from pfdf import watershed

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.raster import Raster
    from pfdf.typing.core import MatrixArray, VectorArray, scalar, shape2d
    from pfdf.typing.segments import Outlets


#####
# Raster Builders
#####


def build(segments, parallel: bool, nprocess: scalar | None) -> MatrixArray:
    "Builds a terminal basin raster sequentially or in parallel, as appropriate"

    # Get the number of processes
    if parallel:
        nprocess = validate.nprocess(nprocess)

    # Run sequentially or in parallel
    if not parallel or nprocess == 1:
        return built_sequentially(segments)
    else:
        return built_in_parallel(segments, nprocess)


def built_sequentially(segments) -> MatrixArray:
    "Builds a terminal basin raster sequentially"

    # Sort terminal outlets from upstream to down
    areas = segments.area(terminal=True)
    indices = np.argsort(areas)

    # Get the outlets in sorted order
    ids, outlets = get_outlets(segments)
    ids = ids[indices]
    sorted = []
    for k in indices:
        sorted.append(outlets[k])

    # Build the raster
    return chunk_raster(ids, sorted, segments.flow)


def built_in_parallel(segments, nprocess: int) -> MatrixArray:
    "Builds a terminal basin raster in parallel"

    # Get the ID and location of each basin outlet, and initialize output raster
    ids, outlets = get_outlets(segments)
    final = new_raster(segments.raster_shape)

    # Count the number of terminal outlets flowing into each terminal basin.
    # Get the unique set of these counts, sorted from downstream to upstream
    nOutlets = count_outlets(segments, outlets)
    counts = np.unique(nOutlets)
    counts = np.flip(counts)

    # Sort basins into groups based on their outlet counts
    groups = []
    for count in counts:
        ingroup = nOutlets == count
        group = (ids[ingroup], filter_outlets(outlets, ingroup))
        groups.append(group)

    # Process each group in parallel. Initialize processes with flow directions
    with Pool(nprocess, initializer, initargs=[segments.flow]) as pool:
        for ids, outlets in groups:
            output = group_rasters(pool, nprocess, ids, outlets)
            update_raster(final, output)
    return final


def group_rasters(
    pool: Pool, nprocess: int, ids: VectorArray, outlets: Outlets
) -> list[MatrixArray]:
    "Builds the rasters for a basin group in parallel chunks"

    chunks = []
    for k in range(nprocess):
        basins = slice(k, None, nprocess)
        chunk = (ids[basins], outlets[basins])
        chunks.append(chunk)
    return pool.starmap(chunk_raster, chunks)


def chunk_raster(
    ids: VectorArray, outlets: Outlets, flow_: Optional[Raster] = None
) -> MatrixArray:
    "Sequentially builds the basin raster for a set of ordered outlets"

    # Collect flow directions. Use global if in a parallel process
    if flow_ is None:
        global flow
    else:
        flow = flow_

    # Initialize basins raster and setup pysheds
    raster = new_raster(flow.shape)
    fdir = flow.as_pysheds()
    grid = Grid.from_raster(fdir)

    # Get catchment mask for each basin. Use to assign pixel values
    for id, (row, col) in zip(ids, outlets, strict=True):
        catchment = grid.catchment(
            fdir=fdir, x=col, y=row, xytype="index", **watershed._FLOW_OPTIONS
        )
        raster[catchment] = id
    return raster


#####
# Utilities
#####


def new_raster(shape: shape2d, dtype: type = "int32") -> MatrixArray:
    return np.zeros(shape, dtype)


def get_outlets(segments) -> tuple[VectorArray, Outlets]:
    "Returns terminal outlet IDs and locations"
    ids = segments.terminal_ids
    outlets = segments.outlets(ids)
    return ids, outlets


def count_outlets(segments, outlets: Outlets) -> VectorArray:
    "Counts the number of terminal outlets that flow into each terminal basin"

    # Build a terminal outlet raster mask
    raster = new_raster(segments.raster_shape, bool)
    for row, col in outlets:
        raster[row, col] = True

    # Compute the number of terminal outlets flowing into each terminal basin
    nOutlets = watershed.accumulation(segments.flow, mask=raster)
    nOutlets = segments.catchment_summary("outlet", nOutlets, terminal=True)
    return nOutlets


def filter_outlets(outlets: Outlets, ingroup: VectorArray) -> Outlets:
    "Returns outlets that are in a group"

    filtered = []
    for outlet, isin in zip(outlets, ingroup, strict=True):
        if isin:
            filtered.append(outlet)
    return filtered


def initializer(flow_: Raster) -> None:
    "Initializes a pool process with a flow directions raster"
    global flow
    flow = flow_


def update_raster(final: MatrixArray, rasters: list[MatrixArray]) -> None:
    "Updates the final raster using rasters from a group processed in parallel"
    for raster in rasters:
        zeros = final == 0
        final[zeros] = raster[zeros]
