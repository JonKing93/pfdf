"""
segments  Determine stream segments worthy of hazard assessment modeling
----------
The segments module provides the "Segments" class. This class provides various
methods for managing the stream segments in a drainage network. Common operations
include:

    * Building a stream segment network
    * Filtering the network to a set of model-worthy segments
    * Calculating values for each segment in the network, and
    * Exporting the network (and associated data value) to file or GeoJSON

Please see the documentation of the Segments class for details on implementing 
these procedures.
----------
Classes:
    Segments    - Builds and manages a stream segment network
"""

from math import inf, nan, sqrt
from typing import Any, Callable, Literal, Optional, Self

import fiona
import geojson
import numpy as np
import rasterio.features
import shapely
from geojson import Feature, FeatureCollection
from rasterio.transform import rowcol

import pfdf._validate.core as validate
from pfdf import watershed
from pfdf._utils import all_nones
from pfdf._utils import basins as _basins
from pfdf._utils import nodata, real
from pfdf._utils.kernel import Kernel
from pfdf._utils.nodata import NodataMask
from pfdf.errors import MissingCRSError, MissingTransformError, ShapeError
from pfdf.projection import CRS, BoundingBox, Transform, _crs
from pfdf.raster import Raster, RasterInput
from pfdf.typing import (
    BasinValues,
    BooleanMatrix,
    FlowNumber,
    MatrixArray,
    Pathlike,
    PixelIndices,
    PropertyDict,
    RealArray,
    ScalarArray,
    SegmentIndices,
    SegmentParents,
    SegmentValues,
    VectorArray,
    scalar,
    shape2d,
    slopes,
    vector,
)

# Type aliases
indices = list[PixelIndices]
Statistic = Literal[
    "outlet",
    "min",
    "max",
    "mean",
    "median",
    "std",
    "sum",
    "var",
    "nanmin",
    "nanmax",
    "nanmean",
    "nanmedian",
    "nanstd",
    "nansum",
    "nanvar",
]
StatFunction = Callable[[np.ndarray], ScalarArray]
FeatureType = Literal["segments", "segment outlets", "outlets", "basins"]
PropertySchema = dict[str, str]

# Supported statistics -- name: (function, description)
_STATS = {
    "outlet": (None, "Values at stream segment outlet pixels"),
    "min": (np.amin, "Minimum value"),
    "max": (np.amax, "Maximum value"),
    "mean": (np.mean, "Mean"),
    "median": (np.median, "Median"),
    "std": (np.std, "Standard deviation"),
    "sum": (np.sum, "Sum"),
    "var": (np.var, "Variance"),
    "nanmin": (np.nanmin, "Minimum value, ignoring NaNs"),
    "nanmax": (np.nanmax, "Maximum value, ignoring NaNs"),
    "nanmean": (np.nanmean, "Mean value, ignoring NaNs"),
    "nanmedian": (np.nanmedian, "Median value, ignoring NaNs"),
    "nanstd": (np.nanstd, "Standard deviation, ignoring NaNs"),
    "nansum": (np.nansum, "Sum, ignoring NaNs"),
    "nanvar": (np.nanvar, "Variance, ignoring NaNs"),
}


class Segments:
    """
    Segments  Builds and manages a stream segment network
    ----------
    The Segments class is used to build and manage a stream segment network. Here,
    a stream segment is approximately equal to the stream bed of a catchment basin.
    The class constructor delineates an initial network. The class then provides
    methods to compute earth-system variables for the individual stream segments,
    and to filter the network to model-worthy segments. Other method compute
    inputs for hazard assessment models, and the "save" method exports results to
    standard GIS file formats. Please see the user guide for more detailed instructions
    on working with this class.
    ----------
    **FOR USERS**
    Object Creation:
        __init__            - Builds an initial stream segment network

    Properties (network):
        length              - The number of segments in the network
        nlocal              - The number of local drainage networks in the full network
        crs                 - The coordinate reference system associated with the network
        crs_units           - The units of the CRS along the X and Y axes

    Properties (segments):
        segments            - A list of shapely.LineString objects representing the stream segments
        lengths             - The length of each segment
        ids                 - A unique integer ID associated with each stream segment
        parents             - The IDs of the upstream parents of each stream segment
        child               - The ID of the downstream child of each stream segment
        isterminus          - Whether each segment is a terminal segment
        indices             - The indices of each segment's pixels in the stream segment raster
        npixels             - The number of pixels in the catchment basin of each stream segment

    Properties (raster metadata):
        flow                - The flow direction raster used to build the network
        raster_shape        - The shape of the flow direction raster
        transform           - The affine transformation associated with the flow raster
        resolution          - The resolution of the flow raster pixels
        pixel_area          - The area of a raster pixel

    Dunders:
        __len__             - The number of segments in the network
        __str__             - A string representing the network
        __geo_interface__   - A geojson-like dict of the network

    Rasters:
        locate_basins       - Builds and saves the basin raster, optionally in parallel
        raster              - Returns a raster representation of the stream segment network
        basin_mask          - Returns the catchment or terminal outlet basin mask for the queried stream segment

    Outlets:
        terminus            - Return the ID of the queried segment's terminal segment
        termini             - Return the IDs of all terminal segments
        outlet              - Return the indices of the queried segment's outlet or terminal outlet pixel
        outlets             - Return the indices of all outlet or terminal outlet pixels

    Generic Statistics:
        statistics          - Print or return info about supported statistics
        summary             - Compute summary statistics over the pixels for each segment
        basin_summary       - Compute summary statistics over the catchment basins or terminal outlet basins

    Specific Variables:
        area                - Computes the total basin areas
        burn_ratio          - Computes the burned proportion of basins
        burned_area         - Computes the burned area of basins
        developed_area      - Computes the developed area of basins
        confinement         - Computes the confinement angle for each segment
        in_mask             - Checks whether each segment is within a mask
        in_perimeter        - Checks whether each segment is within a fire perimeter
        kf_factor           - Computes mean basin KF-factors
        scaled_dnbr         - Computes mean basin dNBR / 1000
        scaled_thickness    - Computes mean basin soil thickness / 100
        sine_theta          - Computes mean basin sin(theta)
        slope               - Computes the mean slope of each segment
        relief              - Computes the vertical relief to highest ridge cell for each segment
        ruggedness          - Computes topographic ruggedness (relief / sqrt(area)) for each segment
        upslope_ratio       - Computes the proportion of basin pixels that meet a criteria

    Filtering:
        copy                - Returns a deep copy of the Segments object
        keep                - Restricts the network to the indicated segments while optionally preserving continuity
        remove              - Removes segments from the network while optionally preserving continuity

    Export:
        geojson             - Returns the network as a geojson.FeatureCollection
        save                - Saves the network to file

    INTERNAL
    Attributes:
        _flow                   - The flow direction raster for the watershed
        _segments               - A list of shapely LineStrings representing the segments
        _ids                    - The ID for each segment
        _indices                - A list of each segment's pixel indices
        _npixels                - The number of catchment pixels for each stream segment
        _child                  - The index of each segment's downstream child
        _parents                - The indices of each segment's upstream parents
        _basins                 - Saved nested drainage basin raster values

    Utilities:
        _indices_to_ids         - Converts segment indices to (user-facing) IDs
        _nbasins                - Returns the number of catchment or terminal outlet basins
        _basin_npixels          - Returns npixels for catchment or terminal outlet basins
        _preallocate            - Initializes an array to hold summary values
        _accumulation           - Computes flow accumulation values

    Generic Validation:
        _validate               - Checks that an input raster has metadata matching the flow raster
        _check_ids              - Checks that IDs are in the network
        _validate_id            - Checks that a segment ID is valid

    Outlets:
        _terminus               - Returns the index of the queried segment's terminus
        _termini                - Returns the indices of all terminal segments
        _outlet                 - Returns the outlet indices for the queried stream segment index

    Rasters:
        _segments_raster        - Builds a stream segment raster array

    Confinement Angles:
        _segment_confinement    - Computes the confinement angle for a stream segment
        _pixel_slopes           - Computes confinement slopes for a pixel

    Summaries:
        _summarize              - Computes a summary statistic
        _values_at_outlets      - Returns the data values at the outlet pixels
        _accumulation_summary   - Computes basin summaries using flow accumulation
        _catchment_summary      - Computes summaries by iterating over basin catchments

    Filtering:
        _validate_selection     - Validates indices/IDs used to select segments for filtering
        _removable              - Locates requested segments on the edges of their local flow networks
        _continuous_removal     - Locates segments that can be removed without breaking flow continuity

    Filtering Updates:
        _update_segments        - Computes updated _segments and _indices after segments are removed
        _update_family          - Updates child-parent arrays in-place after removing segments
        _update_indices         - Updates connectivity indices in-place after removing segments
        _update_connectivity    - Computes updated _child and _parents after segments are removed
        _update_basins          - Resets _basins if terminal basin outlets were removed

    Export:
        _validate_properties    - Checks that a GeoJSON properties dict is valid
        _validate_export        - Checks export properties and type
        _basin_polygons         - Returns a generator of (Polygon, value) geometries
    """

    #####
    # Dunders
    #####

    def __init__(
        self,
        flow: RasterInput,
        mask: RasterInput,
        max_length: scalar = inf,
        base_unit: bool = False,
    ) -> None:
        """
        __init__  Creates a new Segments object
        ----------
        Segments(flow, mask)
        Builds a Segments object to manage the stream segments in a drainage network.
        Note that stream segments approximate the river beds in the catchment basins,
        rather than the full catchment basins. The returned object records the
        pixels associated with each segment in the network.

        The stream segment network is determined using a TauDEM-style D8 flow direction
        raster and a raster mask (and please see the documentation of the pfdf.watershed
        module for details of this style). Note the the flow direction raster must have
        both a CRS and an affine Transform. The mask is used to indicate the pixels under
        consideration as stream segments. True pixels may possibly be assigned to a
        stream segment, False pixels will never be assiged to a stream segment. The
        mask typically screens out pixels with low flow accumulations, and may include
        other screenings - for example, to remove pixels in large bodies of water, or
        pixels below developed areas.

        Segments(..., max_length)
        Segments(..., max_length, base_unit=True)
        Also specifies a maximum length for the segments in the network. Any segment
        longer than this length will be split into multiple pieces. The split pieces
        will all have the same length, which will be <= max_length. Note that the
        max_length must be at least as long as the diagonal of the raster pixels.
        By default, this command interprets max_length in meters. Set base_unit=True
        to specify max_length in the base unit of the affine Transform instead.
        ----------
        Inputs:
            flow: A TauDEM-style D8 flow direction raster
            mask: A raster whose True values indicate the pixels that may potentially
                belong to a stream segment.
            max_length: A maximum allowed length for segments in the network. Units
                should be the same as the units of the (affine) transform for the
                flow raster.
            base_unit: True to interpret the maximum length as the base unit of the
                affine Transform. False (default) to interpret max_length in meters.

        Outputs:
            Segments: A Segments object recording the stream segments in the network.
        """

        # Initialize attributes
        self._flow: Raster = None
        self._segments: list[shapely.LineString] = None
        self._ids: SegmentValues = None
        self._indices: indices = None
        self._npixels: SegmentValues = None
        self._child: SegmentValues = None
        self._parents: SegmentParents = None
        self._basins: Optional[MatrixArray] = None

        # Validate and record flow raster
        flow = Raster(flow, "flow directions")
        if flow.crs is None:
            raise MissingCRSError("The flow direction raster must have a CRS.")
        elif flow.transform is None:
            raise MissingTransformError(
                "The flow direction raster must have an affine Transform."
            )
        self._flow = flow

        # Max length cannot be shorter than a pixel diagonal
        max_length = validate.scalar(max_length, "max_length", dtype=real)
        if not base_unit:
            max_length = _crs.dy_from_meters(flow.crs, max_length)
        if max_length < flow.transform.pixel_diagonal():
            length_m = _crs.dy_to_meters(flow.crs, max_length)
            diagonal_m = flow.transform.pixel_diagonal(meters=True)
            raise ValueError(
                f"max_length (value = {length_m} meters) must be at least as long as the "
                f"diagonals of the pixels in the flow direction raster (length = {diagonal_m} meters)."
            )

        # Calculate network. Assign IDs
        self._segments = watershed.network(self.flow, mask, max_length, base_unit=True)
        self._ids = np.arange(self.size, dtype=int) + 1

        # Initialize attributes - indices, child, parents
        self._indices = []
        self._child = np.full(self.size, -1, dtype=int)
        self._parents = np.full((self.size, 2), -1, dtype=int)

        # Initialize variables used to determine connectivity and split points.
        # (A split point is where a long stream segment was split into 2 pieces)
        starts = np.empty((self.size, 2), float)
        outlets = np.empty((self.size, 2), float)
        split = False

        # Get the spatial coordinates of each segment
        for s, segment in enumerate(self.segments):
            coords = np.array(segment.coords)
            starts[s, :] = coords[0, :]
            outlets[s, :] = coords[-1, :]

            # Get the pixel indices for each segment. If the first two indices are
            # identical, then this is downstream of a split point
            rows, cols = rowcol(
                self.flow.transform.affine, xs=coords[:, 0], ys=coords[:, 1]
            )
            if rows[0] == rows[1] and cols[0] == cols[1]:
                split = True

            # If the segment is downstream of a split point, then remove the
            # first index so that split pixels are assigned to the split segment
            # that contains the majority of the pixel
            if split:
                del rows[0]
                del cols[0]
                split = False

            # If the final two indices are identical, then the next segment
            # is downstream of a split point.
            if rows[-1] == rows[-2] and cols[-1] == cols[-2]:
                split = True

            # Record pixel indices. Remove the final coordinate so that junctions
            # are assigned to the downstream segment.
            indices = (rows[:-1], cols[:-1])
            self._indices.append(indices)

        # Find upstream parents (if any)
        for s, start in enumerate(starts):
            parents = np.equal(start, outlets).all(axis=1)
            parents = np.argwhere(parents)

            # Add extra columns if there are more parents than initially expected
            nextra = parents.size - self._parents.shape[1]
            if nextra > 0:
                fill = np.full((self.size, nextra), -1, dtype=int)
                self._parents = np.concatenate((self._parents, fill), axis=1)

            # Record child-parent relationships
            self._child[parents] = s
            self._parents[s, 0 : parents.size] = parents.flatten()

        # Compute flow accumulation
        self._npixels = self._accumulation()

    def __len__(self) -> int:
        "The number of stream segments in a Segments object"
        return len(self._segments)

    def __str__(self) -> str:
        "String representation of the object"
        return f"A set of {self.size} stream segments in {self.nlocal} local drainage networks."

    @property
    def __geo_interface__(self) -> FeatureCollection:
        "A geojson dict-like representation of the Segments object"
        return self.geojson(type="segments", properties=None)

    #####
    # Properties
    #####

    ##### Network

    @property
    def size(self) -> int:
        "The number of stream segments in the network"
        return len(self)

    @property
    def nlocal(self) -> int:
        "The number of local drainage networks"
        ntermini = np.sum(self.isterminal())
        return int(ntermini)

    @property
    def crs(self) -> CRS:
        "The coordinate reference system of the stream segment network"
        return self._flow.crs

    @property
    def crs_units(self) -> tuple[str, str]:
        "The units of the CRS along the X and Y axes"
        return self._flow.crs_units

    ##### Segments

    @property
    def segments(self) -> list[shapely.LineString]:
        "A list of shapely LineStrings representing the stream segments"
        return self._segments.copy()

    @property
    def ids(self) -> SegmentValues:
        "The ID of each stream segment"
        return self._ids.copy()

    @property
    def terminal_ids(self) -> VectorArray:
        return self.ids[self.isterminal()]

    @property
    def indices(self) -> indices:
        "The row and column indices of the stream raster pixels for each segment"
        return self._indices.copy()

    @property
    def npixels(self) -> SegmentValues:
        "The number of pixels in the catchment basin of each stream segment"
        return self._npixels.copy()

    ##### Raster metadata

    @property
    def flow(self) -> Raster:
        "The flow direction raster used to build the network"
        return self._flow

    @property
    def raster_shape(self) -> shape2d:
        "The shape of the stream segment raster"
        return self._flow.shape

    @property
    def transform(self) -> Transform:
        "The (affine) transform of the stream segment raster"
        return self._flow.transform

    @property
    def bounds(self) -> BoundingBox:
        "The BoundingBox of the stream segment raster"
        return self._flow.bounds

    #####
    # Utilities
    #####

    def _indices_to_ids(self, indices: RealArray) -> RealArray:
        "Converts segment indices to (user-facing) IDs"

        # If empty, just return directly
        indices = np.array(indices, copy=False)
        if indices.size == 0:
            return indices

        # Otherwise, convert to ids
        ids = np.zeros(indices.shape)
        valid = indices != -1
        ids[valid] = self._ids[indices[valid]]
        return ids

    def _basin_npixels(self, terminal: bool) -> BasinValues:
        "Returns the number of pixels in catchment or terminal outlet basins"
        if terminal:
            return self._npixels[self.isterminal()]
        else:
            return self._npixels

    def _nbasins(self, terminal: bool) -> int:
        "Returns the number of catchment or terminal outlet basins"
        if terminal:
            return self.nlocal
        else:
            return self.size

    def _preallocate(self, terminal: bool = False) -> BasinValues:
        "Preallocates an array to hold summary values"
        length = self._nbasins(terminal)
        return np.empty(length, dtype=float)

    def _accumulation(
        self,
        weights: Optional[RasterInput] = None,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
        omitnan: bool = False,
    ) -> BasinValues:
        "Computes flow accumulation values"

        # Default case is just npixels
        if all_nones(weights, mask) and (self._npixels is not None):
            return self._basin_npixels(terminal).copy()

        # Otherwise, compute the accumulation at each outlet
        accumulation = watershed.accumulation(
            self.flow, weights, mask, omitnan=omitnan, check_flow=False
        )
        return self._values_at_outlets(accumulation, terminal=terminal)

    #####
    # Generic Validation
    #####

    def _validate(self, raster: Any, name: str) -> Raster:
        "Checks that an input raster has metadata matching the flow raster"
        return self.flow.validate(raster, name)

    def _check_ids(self, ids: VectorArray, name: str) -> None:
        "Checks that segment IDs are in the network"

        validate.integers(ids, name)
        for i, id in enumerate(ids):
            if id not in self._ids:
                if name == "ids":
                    name = f"{name}[{i}]"
                raise ValueError(
                    f"{name} (value={id}) is not the ID of a segment in the network. "
                    "See the '.ids' property for a list of current segment IDs."
                )

    def _validate_id(self, id: Any) -> int:
        "Checks that a segment ID is valid and returns index"
        id = validate.scalar(id, "id", dtype=real)
        id = id.reshape(1)
        self._check_ids(id, "id")
        index = np.argwhere(self._ids == id)
        return int(index[0, 0])

    def _validate_ids(self, ids: Any) -> VectorArray:
        """Checks that a set of segment IDs are valid and converts to linear
        indices. If no IDs are provided, returns all indices in the network"""

        # Select all indices if unspecified. Otherwise validate
        if ids is None:
            return np.arange(self.size)

        # Validate
        ids = validate.vector(ids, "ids", dtype=real)
        self._check_ids(ids, "ids")

        # Convert IDs to indices
        indices = np.empty(ids.shape, int)
        for k, id in enumerate(ids):
            indices[k] = np.argwhere(id == self.ids)
        return indices

    #####
    # Outlets
    #####

    def isterminal(self, ids: Optional[vector] = None) -> VectorArray:
        """
        Indicates whether segments are terminal segments
        ----------
        self.isterminal()
        Determines whether each segment is a terminal segment or not. A segment
        is terminal if it does not have a downstream child. (Note that there may
        still be other segments downstream if the segment is in a nested drainage
        network). Returns a boolean 1D numpy array with one element per segment
        in the network. True elements indicate terminal segments, False elements
        are segments that are not terminal.

        self.isterminal(ids)
        Determines whether the queried segments are terminal segments or not.
        Returns a boolean 1D array with one element per queried segment.
        ----------
        Inputs:
            ids: The IDs of segments being queried. If not set, queries all segments
                in the network.

        Outputs:
            boolean 1D numpy array: Whether each segment is terminal.
        """

        indices = self._validate_ids(ids)
        return self._child[indices] == -1

    def termini(self, ids: Optional[vector] = None) -> VectorArray:
        """
        Returns the IDs of terminal segments
        ----------
        self.termini()
        Determines the ID of the terminal segment for each stream segment in the
        network. Returns a numpy 1D array with one element per stream segment.
        Typically, many segments will drain to the same terminal segment, so this
        array will usually contain many duplicate IDs.

        If you instead want the IDs of all the terminal segments, use:
            >>> self.terminal_ids

        self.termini(ids)
        Only returns terminal segment IDs for the queried segments. The output
        array will have one element per queried segment.
        ----------
        Inputs:
            ids: The IDs of the queried segments. If not set, then queries every
                segment in the network.

        Outputs:
            numpy 1D array: The ID of the terminal segment for each queried segment
        """

        # Walk downstream to locate the terminal index for each queried segment
        indices = self._validate_ids(ids)
        termini = []
        for index in indices:
            while self._child[index] != -1:
                index = self._child[index]
            termini.append(index)

        # Return as a numpy array of IDs
        termini = np.array(termini).reshape(-1)
        return self._indices_to_ids(termini)

    def outlets(
        self,
        ids: Optional[vector] = None,
        segment_outlets: bool = False,
        as_array: bool = False,
    ) -> list[tuple[int, int]] | MatrixArray:
        """
        Returns the row and column indices of outlet pixels
        ----------
        self.outlets()
        Returns the row and column index of the terminal outlet pixel for each
        segment in the network. Returns a list with one element per segment in
        the network. Each element is a tuple of two integers. The first element
        is the row index of the outlet pixel in the stream network raster, and
        the second element is the column index.

        self.outlets(ids)
        Only returns outlet pixel indices for the queried segments. The output
        list will have one element per queried segment.

        self.outlets(..., segment_outlets=True)
        Returns the indices of each segment's immediate outlet pixel, rather than
        the indices of the terminal outlet pixels. Each segment outlet is the final
        pixel in the stream segment itself. (Compare with a terminal outlet, which
        is the final pour point in the segment's local drainage network).

        self.outlets(..., as_array=True)
        Returns the outlet pixel indices as a numpy array, rather than as a list.
        The output array will have one row per queried stream segment, and two
        columns. The first column is the row indices, and the second column is
        the column indices.
        ----------
        Inputs:
            ids: The IDs of the queried stream segments. If not set, queries all
                segments in the network.
            segment_outlets: True to return the indices of each stream segment's
                outlet pixel. False (default) to return the indices of terminal
                outlet pixels
            as_array: True to return the pixel indices as an Nx2 numpy array.
                False (default) to return indices as a list of 2-tuples.

        Outputs:
            list[tuple[int, int]] | numpy array: The outlet pixel indices of the
                queried stream segments
        """

        # Get the indices of the appropriate segments
        if not segment_outlets:
            ids = self.termini(ids)
        indices = self._validate_ids(ids)

        # Extract outlet pixel indices
        outlets = []
        for index in indices:
            pixels = self._indices[index]
            row = pixels[0][-1]
            column = pixels[1][-1]
            outlets.append((row, column))

        # Optionally convert to array
        if as_array:
            outlets = np.array(outlets).reshape(-1, 2)
        return outlets

    #####
    # Local Networks
    #####

    def _get_parents(self, index: int) -> list[int]:
        "Gets the indices of parent segments"
        parents = self._parents[index, :]
        return [index for index in parents if index != -1]

    def parents(self, id: scalar) -> list[int] | None:
        """
        Returns the IDs of the queried segment's parent segments
        ----------
        self.parents(id)
        Given a stream segment ID, returns the IDs of the segment's parents. If
        the segment has parents, returns a list of IDs. If the segment does not
        have parents, returns None.
        ----------
        Inputs:
            id: The queried stream segment

        Outputs:
            list[int] | None: The IDs of the parent segments
        """

        index = self._validate_id(id)
        parents = self._get_parents(index)
        if len(parents) == 0:
            return None
        else:
            parents = self._indices_to_ids(parents)
            return parents.tolist()

    def child(self, id: scalar) -> int | None:
        """
        Returns the ID of the queried segment's child segment
        ----------
        self.child(id)
        Given a stream segment ID, returns the ID of the segment's child segment
        as an int. If the segment does not have a child, returns None.
        ----------
        Inputs:
            id: The ID of the queried segment

        Outputs:
            int | None: The ID of the segment's child
        """

        index = self._validate_id(id)
        child = self._child[index]
        if child == -1:
            return None
        else:
            child = self._indices_to_ids(child)
            return int(child)

    def ancestors(self, id: scalar) -> VectorArray:
        """
        Returns the IDs of all upstream segments in a local drainage network
        ----------
        self.ancestors(id)
        For a queried stream segment ID, returns the IDs of all upstream segments
        in the local drainage network. These are the IDs of the queried segment's
        parents, the IDs of the parents parents, etc. If the queried segment does
        not have any parent segments, returns an empty array.
        ----------
        Inputs:
            id: The ID of a stream segment in the network

        Outputs:
            numpy 1D array: The IDs of all segments upstream of the queried segment
                within the local drainage network.
        """

        # Validate ID and initial ancestors with immediate parents
        segment = self._validate_id(id)
        ancestors = self._get_parents(segment)

        # Recursively add parents of parents
        k = 0
        while k < len(ancestors):
            index = ancestors[k]
            upstream = self._get_parents(index)
            ancestors += upstream
            k += 1

        # Convert indices to IDs and return as array
        ancestors = np.array(ancestors).reshape(-1)
        return self._indices_to_ids(ancestors)

    def descendents(self, id: scalar) -> VectorArray:
        """
        Returns the IDs of all downstream segments in a local drainage network
        ----------
        self.descendents(id)
        For a queried stream segment, returns the IDs of all downstream segments
        in the queried segment's local drainage network. This is the ID of any
        child segment, the child of that child, etc. If the queried segment does
        not have any descendents, then the returned array will be empty.
        ----------
        Inputs:
            id: The ID of the queried stream segment

        Outputs:
            numpy 1D array: The IDs of all downstream segments in the local
                drainage network.
        """

        # Validate ID and initialize descendent list
        segment = self._validate_id(id)
        descendents = []

        # Recursively add children of children
        child = self._child[segment]
        while child != -1:
            descendents.append(child)
            segment = child
            child = self._child[segment]

        # Convert to IDs and return as array
        descendents = np.array(descendents).reshape(-1)
        return self._indices_to_ids(descendents)

    def family(self, id: scalar) -> VectorArray:
        """
        Return the IDs of stream segments in a local drainage network
        -----------
        self.family(id)
        Returns the IDs of all stream segments in the queried segment's local
        drainage network. These are all segments in the local network that flow
        into the queried segment's outlet, including the queried segment itself.
        Note that the returned IDs may include segments that are neither ancestors
        nor descendents of the queried segment, as the network may contain multiple
        branches draining to the same outlet.
        -----------
        Inputs:
            id: The ID of the queried stream segment

        Outputs:
            numpy 1D array: The IDs of all segments in the local drainage network.
        """

        # Locate segments in the local drainage network
        self._validate_id(id)
        terminus = self.termini(id)
        upstream = self.ancestors(terminus)

        # Group into family array
        family = np.empty(upstream.size + 1, upstream.dtype)
        family[0] = terminus
        family[1:] = upstream
        return family

    def isnested(self, ids: Optional[vector] = None) -> SegmentIndices:
        """
        Determines which segments are in nested drainage basins
        ----------
        self.isnested()
        Identifies segments in nested drainage basins. A nested drainage basin is
        a local drainage network that flows into another local drainage network
        further downstream. Nesting is an indication of flow discontinuity.
        Returns a 1D boolean numpy array with one element per stream segment.
        True elements indicate segments in nested networks. False elements are
        segments not in a nested network.

        self.isnested(ids)
        Determines whether the queried segments are in nested drainage basins.
        The output array will have one element per queried segment.
        ----------
        Inputs:
            ids: The IDs of the segments being queried. If unset, queries all
                segments in the network.

        Outputs:
            boolean 1D numpy array: Whether each segment is in a nested drainage
                network
        """

        # Get the unique set of outlet IDs for the queried segments
        termini = self.termini(ids)
        outlet_ids = np.unique(termini)

        # Get the basin IDs and identify nested outlets
        outlets = self.outlets(outlet_ids, as_array=True)
        basins = self._locate_basins()
        basin_ids = basins[outlets[:, 0], outlets[:, 1]]
        nested_outlets = outlet_ids[outlet_ids != basin_ids]
        return np.isin(termini, nested_outlets)

    #####
    # Rasters
    #####

    def basin_mask(self, id: scalar, terminal: bool = False) -> Raster:
        """
        basin_mask  Return a mask of the queried segment's catchment or terminal outlet basin
        ----------
        self.basin_mask(id)
        Returns the catchment basin mask for the queried segment. The catchment
        basin consists of all pixels that drain into the segment. The output will
        be a boolean raster whose True elements indicate pixels that are in the
        catchment basin.

        self.basin_mask(id, terminal=True)
        Returns the mask of the queried segment's terminal outlet basin. The
        terminal outlet basin is the catchment basin for the segment's local
        drainage network. This basin is a superset of the segment's catchment
        basin. The output will be a boolean raster whose True elements indicate
        pixels that are in the local drainage basin.
        ----------
        Inputs:
            id: The ID of the stream segment whose basin mask should be determined
            terminal: True to return the terminal outlet basin mask for the segment.
                False (default) to return the catchment mask.

        Outputs:
            Raster: The boolean raster mask for the basin. True elements indicate
                pixels that belong to the basin.
        """

        self._validate_id(id)
        [[row, column]] = self.outlets(id, segment_outlets=not terminal)
        return watershed.catchment(self.flow, row, column, check_flow=False)

    def raster(self, basins=False) -> Raster:
        """
        raster  Return a raster representation of the stream network
        ----------
        self.raster()
        Returns the stream segment raster for the network. This raster has a 0
        background. Non-zero pixels indicate stream segment pixels. The value of
        each pixel is the ID of the associated stream segment.

        self.raster(basins=True)
        Returns the terminal outlet basin raster for the network. This raster has
        a 0 background. Non-zero pixels indicate terminal outlet basin pixels. The
        value of each pixel is the ID of the terminal segment associated with the
        basin. If a pixel is in multiple basins, then its value to assigned to
        the ID of the terminal segment that is farthest downstream.

        Note that you can use Segments.locate_basins to pre-build the raster
        before calling this command. If not pre-built, then this command will
        generate the terminal basin raster sequentially, which may take a while.
        Note that the "locate_basins" command includes options to parallelize
        this process, which may improve runtime.
        ----------
        Inputs:
            basins: False (default) to return the stream segment raster. True to
                return a terminal basin raster

        Outputs:
            Raster: A stream segment raster, or terminal outlet basin raster.
        """

        if basins:
            raster = self._locate_basins()
        else:
            raster = self._segments_raster()
        return Raster.from_array(
            raster, nodata=0, crs=self.crs, transform=self.transform, copy=False
        )

    def locate_basins(
        self, parallel: bool = False, nprocess: Optional[scalar] = None
    ) -> None:
        """
        locate_basins  Builds and saves a terminal basin raster, optionally in parallel
        ----------
        self.locate_basins()
        Builds the terminal basin raster and saves it internally. The saved
        raster will be used to quickly implement other commands that require it.
        (For example, Segments.raster, Segments.geojson, and Segments.save).
        Note that the saved raster is deleted if any of the terminal outlets are
        removed from the Segments object, so it is usually best to call this
        command *after* filtering the network.

        self.locate_basins(parallel=True)
        self.locate_basins(parallel=True, nprocess)
        Building a basin raster is computationally difficult and can take a while
        to run. Setting parallel=True allows this process to run on multiple CPUs,
        which can improve runtime. However, the use of this option imposes two
        restrictions:

        * You cannot use the "parallel" option from an interactive python session.
          Instead, the pfdf code MUST be called from a script via the command line.
          For example, something like:  $ python -m my_script
        * The code in the script must be within a
            if __name__ == "__main__":
          block. Otherwise, the parallel processes will attempt to rerun the script,
          resulting in an infinite loop of CPU process creation.

        By default, setting parallel=True will create a number of parallel processes
        equal to the number of CPUs - 1. Use the nprocess option to specify a
        different number of parallel processes. Note that you can obtain the number
        of available CPUs using os.cpu_count(). Also note that parallelization
        options are ignored if only 1 CPU is available.
        ----------
        Inputs:
            parallel: True to build the raster in parallel. False (default) to
                build sequentially.
            nprocess: The number of parallel processes. Must be a scalar, positive
                integer. Default is the number of CPUs - 1.
        """

        if self._basins is None:
            self._basins = _basins.build(self, parallel, nprocess)

    def _locate_basins(self):
        "Returns basin raster array values"
        self.locate_basins()
        return self._basins

    def _segments_raster(self) -> MatrixArray:
        "Builds a stream segment raster array"
        raster = np.zeros(self._flow.shape, dtype="int32")
        for id, (rows, cols) in zip(self._ids, self._indices):
            raster[rows, cols] = id
        return raster

    #####
    # Confinement angles
    #####

    def confinement(
        self,
        dem: RasterInput,
        neighborhood: scalar,
        dem_per_m: Optional[scalar] = None,
    ) -> SegmentValues:
        """
        confinement  Returns the mean confinement angle of each stream segment
        ----------
        self.confinement(dem, neighborhood)
        Computes the mean confinement angle for each stream segment. Returns these
        angles as a numpy 1D array. The order of angles matches the order of
        segment IDs in the object.

        The confinement angle for a given pixel is calculated using the slopes in the
        two directions perpendicular to stream flow. A given slope is calculated using
        the maximum DEM height within N pixels of the processing pixel in the
        associated direction. Here, the number of pixels searched in each direction
        (N) is equivalent to the "neighborhood" input. The slope equation is thus:

            slope = max height(N pixels) / (N * length)

        where length is one of the following:
            * X axis resolution (for flow along the Y axis)
            * Y axis resolution (for flow along the X axis)
            * length of a raster cell diagonal (for diagonal flow)
        Recall that slopes are computed perpendicular to the flow direction,
        hence the use X axis resolution for Y axis flow and vice versa.

        The confinment angle is then calculated using:

            theta = 180 - tan^-1(slope1) - tan^-1(slope2)

        and the mean confinement angle is calculated over all the pixels in the
        stream segment.

        Example:
        Consider a pixel flowing east with neighborhood=4. (East here indicates
        that the pixel is flowing to the next pixel on its right - it is not an
        indication of actual geospatial directions). Confinement angles are then
        calculated using slopes to the north and south. The north slope is
        determined using the maximum DEM height in the 4 pixels north of the
        stream segment pixel, such that:

            slope = max height(4 pixels north) / (4 * Y axis resolution)

        and the south slope is computed similarly. The two slopes are used to
        compute the confinement angle for the pixel, and this process is then
        repeated for all pixels in the stream segment. The final value for the
        stream segment will be the mean of these values.

        self.confinement(..., dem_per_m)
        By default, this routine assumes that the DEM units are meters. If this
        is not the case, then use the "dem_per_m" to specify a conversion factor
        between the unit systems. This factor is essential to accurately compute
        confinement angle slopes, so neglecting it will result in incorrect
        confinement angles.
        ----------
        Inputs:
            dem: A raster of digital elevation model (DEM) data. Should have
                square pixels.
            neighborhood: The number of raster pixels to search for maximum heights.
                Must be a positive integer.
            dem_per_m: A conversion factor for when the DEM uses units other than meters.

        Outputs:
            numpy 1D array: The mean confinement angle for each stream segment.
        """

        # Validate
        neighborhood = validate.scalar(neighborhood, "neighborhood", real)
        validate.positive(neighborhood, "neighborhood")
        validate.integers(neighborhood, "neighborhood")
        dem_per_m = validate.conversion(dem_per_m, "dem_per_m")
        dem = self._validate(dem, "dem")

        # Preallocate. Initialize kernel
        theta = self._preallocate()
        kernel = Kernel(neighborhood, *self.raster_shape)

        # Get the pixel length scaling factor
        scale = neighborhood
        if dem_per_m is not None:
            scale = scale * dem_per_m

        # Determine flow lengths in the units of the DEM
        width, height = self.transform.resolution(meters=True)
        lengths = {
            "horizontal": width * scale,
            "vertical": height * scale,
            "diagonal": sqrt(width**2 + height**2) * scale,
        }

        # Get the mean confinement angle for each stream segment
        for i, pixels in enumerate(self._indices):
            theta[i] = self._segment_confinement(pixels, lengths, kernel, dem)
        return theta

    def _segment_confinement(
        self,
        pixels: PixelIndices,
        lengths: dict[str, float],
        kernel: Kernel,
        dem: Raster,
    ) -> ScalarArray:
        "Computes the mean confinement angle for a stream segment"

        # Get the flow directions. If any are NoData, set confinement to NaN
        flows = self.flow.values[pixels]
        if nodata.isin(flows, self.flow.nodata):
            return nan

        # Group indices by pixel. Preallocate slopes
        pixels = np.stack(pixels, axis=-1)
        npixels = pixels.shape[0]
        slopes = np.empty((npixels, 2), dtype=float)

        # Get the slopes for each pixel
        for p, flow, rowcol in zip(range(npixels), flows, pixels):
            slopes[p, :] = self._pixel_slopes(flow, lengths, rowcol, kernel, dem)

        # Compute the mean confinement angle
        theta = np.arctan(slopes)
        theta = np.mean(theta, axis=0)
        theta = np.sum(theta)
        return 180 - np.degrees(theta)

    @staticmethod
    def _pixel_slopes(
        flow: FlowNumber,
        lengths: dict[str, float],
        rowcol: tuple[int, int],
        kernel: Kernel,
        dem: Raster,
    ) -> slopes:
        "Computes the slopes perpendicular to flow for a pixel"

        # Get the perpendicular flow length
        if flow in [1, 5]:
            length = lengths["vertical"]
        elif flow in [3, 7]:
            length = lengths["horizontal"]
        else:
            length = lengths["diagonal"]

        # Update the kernel and compute slopes
        kernel.update(*rowcol)
        return kernel.orthogonal_slopes(flow, length, dem)

    #####
    # Generic summaries
    #####

    @staticmethod
    def statistics(asdict: bool = False) -> dict[str, str] | None:
        """
        statistics  Prints or returns info about supported statistics
        ----------
        Segments.statistics()
        Prints information about supported statistics to the console. The printed
        text is a table with two columns. The first column holds the names of
        statistics that can be used with the "summary" and "basin_summary" methods.
        The second column is a description of each statistic.

        Segments.statistics(asdict=True)
        Returns info as a dict, rather than printing to console. The keys of the
        dict are the names of the statistics. The values are the descriptions.
        ----------
        Inputs:
            asdict: True to return info as a dict. False (default) to print info
                to the console.

        Outputs:
            None | dict[str,str]: None if printing to console. Otherwise a dict
                whose keys are statistic names, and values are descriptions.
        """

        if asdict:
            return {name: values[1] for name, values in _STATS.items()}
        else:
            print("Statistic | Description\n" "--------- | -----------")
            for name, values in _STATS.items():
                description = values[1]
                print(f"{name:9} | {description}")

    @staticmethod
    def _summarize(
        statistic: StatFunction, raster: Raster, indices: PixelIndices | BooleanMatrix
    ) -> ScalarArray:
        """Compute a summary statistic over indicated pixels. Converts NoData elements
        to NaN. Returns NaN if no data elements are selected or all elements are NaN"""

        # Get the values. Require float with at least 1 dimension
        values = raster.values[indices].astype(float)
        values = np.atleast_1d(values)

        # Set NoData values to NaN
        nodatas = NodataMask(values, raster.nodata)
        values = nodatas.fill(values, nan)

        # Return NaN if there's no data, or if everything is already NaN.
        # Otherwise, compute the statistic
        if (values.size == 0) or np.isnan(values).all():
            return np.array(nan)
        else:
            return statistic(values).reshape(1)[0]

    def _values_at_outlets(self, raster: Raster, terminal: bool = False) -> BasinValues:
        "Returns the values at segment outlets. Returns NoData values as NaN"

        identity = lambda input: input
        values = self._preallocate(terminal)
        if terminal:
            ids = self.terminal_ids
        else:
            ids = self.ids
        outlets = self.outlets(ids, segment_outlets=True)
        for k, outlet in enumerate(outlets):
            values[k] = self._summarize(identity, raster, indices=outlet)
        return values

    def summary(self, statistic: Statistic, values: RasterInput) -> SegmentValues:
        """
        summary  Computes a summary value for each stream segment
        ----------
        self.summary(statistic, values)
        Computes a summary statistic for each stream segment. Each summary
        value is computed over the associated stream segment pixels. Returns
        the statistical summaries as a numpy 1D array with one element per segment.

        Note that NoData values are converted to NaN before computing statistics.
        If using one of the statistics that ignores NaN values (e.g. nanmean),
        a segment's summary value will still be NaN if every pixel in the stream
        segment is NaN.
        ----------
        Inputs:
            statistic: A string naming the requested statistic. See Segments.statistics()
                for info on supported statistics
            values: A raster of data values over which to compute stream segment
                summary values.

        Outputs:
            numpy 1D array: The summary statistic for each stream segment
        """

        # Validate
        statistic = validate.option(statistic, "statistic", allowed=_STATS.keys())
        values = self._validate(values, "values raster")

        # Either get outlet values...
        if statistic == "outlet":
            return self._values_at_outlets(values)

        # ...or compute a statistical summary
        statistic = _STATS[statistic][0]
        summary = self._preallocate()
        for i, pixels in enumerate(self._indices):
            summary[i] = self._summarize(statistic, values, pixels)
        return summary

    def basin_summary(
        self,
        statistic: Statistic,
        values: RasterInput,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
    ) -> BasinValues:
        """
        basin_summary  Computes a summary statistic over each catchment or terminal outlet basin
        ----------
        self.basin_summary(statistic, values)
        Computes the indicated statistic over the catchment basin pixels for each
        stream segment. Uses the input values raster as the data value for each pixel.
        Returns a numpy 1D array with one element per stream segment.

        Note that NoData values are converted to NaN before computing statistics.
        If using one of the statistics that ignores NaN values (e.g. nanmean),
        a basin's summary value will still be NaN if every pixel in the basin
        basin is NaN.

        When possible, we recommend only using the "outlet", "mean", "sum", "nanmean",
        and "nansum" statistics when computing summaries for every catchment basin.
        The remaining statistics require a less efficient algorithm, and so are much
        slower to compute. Alternatively, see below for an option to only compute
        statistics for terminal outlet basins - this is typically a faster operation,
        and more suitable for other statistics.

        self.basin_summary(statistic, values, mask)
        Computes masked statistics over the catchment basins. True elements in the
        mask indicate pixels that should be included in statistics. False elements
        are ignored. If a catchment does not contain any True pixels, then its
        summary statistic is set to NaN. Note that a mask will have no effect
        on the "outlet" statistic.

        self.basin_summary(..., terminal=True)
        Only computes statistics for the terminal outlet basins. The output will
        have one element per terminal segment. The order of values will match the
        order of IDs reported by the "Segments.termini" method. The number of
        terminal outlet basins is often much smaller than the total number of
        segments. As such, this option presents a faster alternative and is
        particularly suitable when computing statistics other than "outlet",
        "mean", "sum", "nanmean", or "nansum".
        ----------
        Inputs:
            statistic: A string naming the requested statistic. See Segments.statistics()
                for info on supported statistics.
            values: A raster of data values over which to compute basin summaries
            mask: An optional raster mask for the data values. True elements
                are used to compute basin statistics. False elements are ignored.
            terminal: True to only compute statistics for terminal outlet basins.
                False (default) to compute statistics for every catchment basin.

        Outputs:
            numpy 1D array: The summary statistic for each basin
        """

        # Validate
        statistic = validate.option(statistic, "statistic", allowed=_STATS.keys())
        values = self._validate(values, "values raster")
        if mask is not None:
            mask = self._validate(mask, "mask")
            mask = validate.boolean(mask.values, mask.name, ignore=mask.nodata)

        # Outlet values
        if statistic == "outlet":
            return self._values_at_outlets(values, terminal)

        # Sum or mean are derived from accumulation
        elif statistic in ["sum", "mean", "nansum", "nanmean"]:
            return self._accumulation_summary(statistic, values, mask, terminal)

        # Anything else needs to iterate through basin catchments
        else:
            return self._catchment_summary(statistic, values, mask, terminal)

    def _accumulation_summary(
        self,
        statistic: Literal["sum", "mean", "nansum", "nanmean"],
        values: Raster,
        mask: BooleanMatrix | None,
        terminal: bool,
    ) -> BasinValues:
        "Uses flow accumulation to compute basin summaries"

        # Note whether the summary should omit NaN and NoData values
        if "nan" not in statistic:
            omitnan = False
        else:
            omitnan = True

            # A mask is required to omit NaNs. Initialize if not provided.
            if mask is None:
                mask = np.ones(values.shape, dtype=bool)

            # Update the mask to ignore pixels that are NoData or NaN
            nodatas = NodataMask(values.values, values.nodata)
            if not nodatas.isnan(values.nodata):
                nodatas = nodatas | np.isnan(values.values)
            nodatas.fill(mask, False)

        # Compute sums and pixels counts. If there are no pixels, the statistic is NaN
        sums = self._accumulation(values, mask=mask, terminal=terminal, omitnan=omitnan)
        npixels = self._accumulation(mask=mask, terminal=terminal)
        sums[npixels == 0] = nan

        # Return the sum or mean, as appropriate
        if "sum" in statistic:
            return sums
        else:
            return sums / npixels

    def _catchment_summary(
        self,
        statistic: Statistic,
        values: Raster,
        mask: Raster | None,
        terminal: bool,
    ) -> BasinValues:
        "Iterates through basin catchments to compute summaries"

        # Get statistic, preallocate, and locate catchment outlets
        statistic = _STATS[statistic][0]
        summary = self._preallocate(terminal=terminal)
        ids = self.ids
        if terminal:
            ids = ids[self.isterminal()]
        outlets = self.outlets(ids, segment_outlets=True)

        # Iterate through catchment basins and compute summaries
        for k, outlet in enumerate(outlets):
            catchment = watershed.catchment(self.flow, *outlet, check_flow=False)
            catchment = catchment.values
            if mask is not None:
                catchment = catchment & mask
            summary[k] = self._summarize(statistic, values, catchment)
        return summary

    #####
    # Earth system variables
    #####

    def length(self, base_unit: bool = False) -> SegmentValues:
        """
        Returns the length of each stream segments
        ----------
        self.length()
        self.length(base_unit=True)
        Returns the lengths of the stream segments in the network. By default,
        returns lengths in meters. Set base_unit=True to return lengths in the
        base unit of the CRS instead.
        ----------
        Inputs:
            base_unit: True to return segment lengths in the base unit of the CRS.
                False (default) to return lengths in meters.

        Outputs:
            numpy 1D array: The lengths of the segments in the network
        """
        lengths = np.array([segment.length for segment in self._segments])
        if not base_unit:
            lengths = _crs.dy_to_meters(self.crs, lengths)
        return lengths

    def area(
        self,
        mask: Optional[RasterInput] = None,
        base_unit: bool = False,
        terminal: bool = False,
    ) -> BasinValues:
        """
        area  Returns total catchment areas
        ----------
        self.area()
        self.area(..., base_unit=True)
        Computes the total area of the catchment basin for each stream segment.
        By default, returns areas in kilometers^2. Set base_unit=True to instead
        return areas in the base unit of the CRS squared.

        self.area(mask)
        Computes masked areas for the basins. True elements in the mask indicate
        pixels that should be included in the calculation of areas. False pixels
        are ignored and given an area of 0. Nodata elements are interpreted as False.

        self.area(..., terminal=True)
        Only returns values for the terminal outlet basins.
        ----------
        Inputs:
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute upslope areas.
            base_unit: True to return areas in the base unit of the CRS squared.
                False (default) to return areas in square kilometers.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The catchment area for each stream segment
        """

        # Get the number of pixels
        if mask is None:
            N = self._basin_npixels(terminal)
        else:
            N = self._accumulation(mask=mask, terminal=terminal)

        # Convert to area
        kilometers = not base_unit
        area = N * self.transform.pixel_area(meters=kilometers)
        if kilometers:
            area = area / 1e6
        return area

    def burn_ratio(self, isburned: RasterInput, terminal: bool = False) -> BasinValues:
        """
        burn_ratio  Returns the proportion of burned pixels in basins
        ----------
        self.burn_ratio(isburned)
        Given a mask of burned pixel locations, determines the proportion of
        burned pixels in the catchment basin of each stream segment. Returns a numpy
        1D array with the ratio for each segment. Ratios are on the interval from
        0 to 1.

        self.burn_ratio(isburned, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            isburned: A raster mask whose True elements indicate the locations
                of burned pixels in the watershed.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The proportion of burned pixels in each basin
        """
        return self.upslope_ratio(isburned, terminal)

    def burned_area(
        self, isburned: RasterInput, base_unit: bool = False, terminal: bool = False
    ) -> BasinValues:
        """
        burned_area  Returns the total burned area of basins
        ----------
        self.burned_area(isburned)
        self.burned_area(..., base_unit=True)
        Given a mask of burned pixel locations, returns the total burned area in
        the catchment of each stream segment. Returns a numpy 1D array with the
        burned area for each segment. By default, areas are returned in square
        kilometers. Set base_unit=True to instead return ares in the base unit
        of the CRS squared.

        self.burned_area(..., terminal=True)
        Only computes areas for the terminal outlet basins.
        ----------
        Inputs:
            isburned: A raster mask whose True elements indicate the locations of
                burned pixels within the watershed
            base_unit: True to return areas in the base unit of the CRS squared.
                False (default) to return areas in square kilometers.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The burned catchment area for the basins
        """
        return self.area(isburned, base_unit, terminal)

    def developed_area(
        self, isdeveloped: RasterInput, base_unit: bool = False, terminal: bool = False
    ) -> BasinValues:
        """
        developed_area  Returns the total developed area of basins
        ----------
        self.developed_area(isdeveloped)
        self.developed_area(..., kilometers=True)
        Given a mask of developed pixel locations, returns the total developed
        area in the catchment of each stream segment. Returns a numpy 1D array
        with the developed area for each segment. By default, returns areas in
        square kilometers. Set base_unit=True to instead return areas in the base
        unit of the CRS squared.

        self.developed_area(..., terminal)
        Only computes areas for the terminal outlet basins.
        ----------
        Inputs:
            isdeveloped: A raster mask whose True elements indicate the locations
                of developed pixels within the watershed.
            base_unit: True to return areas in the base unit of the CRS squared.
                False (default) to return areas in square kilometers.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The developed catchment area for each basin
        """
        return self.area(isdeveloped, base_unit, terminal)

    def in_mask(self, mask: RasterInput, terminal: bool = False) -> SegmentIndices:
        """
        Determines whether segments have pixels within a mask
        ----------
        self.in_mask(mask)
        self.in_mask(mask, terminal=True)
        Given a raster mask, returns a boolean 1D numpy array with one element
        per segment. True elements indicate segments that have at least one pixel
        within the mask. False elements have no pixels within the mask. If
        terminal=True, only returns values for the terminal segments.
        ----------
        Inputs:
            mask: A raster mask for the watershed.
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            boolean 1D numpy array: Whether each segment has at least one pixel
                within the mask.
        """

        mask = self._validate(mask, "nmask")
        validate.boolean(mask.values, "mask", ignore=mask.nodata)
        isin = self.summary("nanmax", mask) == 1
        if terminal:
            isin = isin[self.isterminal()]
        return isin

    def in_perimeter(
        self, perimeter: RasterInput, terminal: bool = False
    ) -> SegmentIndices:
        """
        Determines whether segments have pixels within a fire perimeter
        ----------
        self.in_perimeter(perimeter)
        self.in_perimeter(perimeter, terminal=True)
        Given a fire perimeter mask, returns a boolean 1D numpy array with one
        element per segment. True elements indicate segments that have at least
        one pixel within the fire perimeter. False elements have no pixels within
        the mask. If terminal=True, only returns values for the terminal segments.
        ----------
        Inputs:
            perimeter: A fire perimeter raster mask
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            boolean 1D numpy array: Whether each segment has at least one pixel
                within the fire perimeter.
        """
        return self.in_mask(perimeter, terminal)

    def kf_factor(
        self,
        kf_factor: RasterInput,
        mask: Optional[RasterInput] = None,
        *,
        terminal: bool = False,
        omitnan: bool = False,
    ) -> BasinValues:
        """
        kf_factor  Computes mean soil KF-factor for basins
        ----------
        self.kf_factor(kf_factor)
        Computes the mean catchment KF-factor for each stream segment in the
        network. Note that the KF-Factor raster must have all positive values.
        If a catchment basin contains NaN or NoData values, then its mean KF-Factor
        is set to NaN.

        self.kf_factor(kf_factor, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean KF-Factors. False elements are ignored. If a
        basin only contains False elements, then its mean Kf-factor is set
        to NaN.

        self.kf_factor(..., *, omitnan=True)
        Ignores NaN and NoData values when computing mean KF-factors. If a basin
        only contains NaN and/or NoData values, then its mean KF-factor will still
        be NaN.

        self.kf_factor(..., *, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            kf_factor: A raster of soil KF-factor values. Cannot contain negative
                elements.
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute mean KF-factors
            omitnan: True to ignore NaN and NoData values. If False (default),
                any basin with (unmasked) NaN or NoData values will have its mean
                Kf-factor set to NaN.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean catchment KF-Factor for each basin
        """

        # Validate
        kf_factor = self._validate(kf_factor, "kf_factor")
        validate.positive(kf_factor.values, "kf_factor", ignore=[kf_factor.nodata, nan])

        # Summarize
        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        return self.basin_summary(
            method,
            kf_factor,
            mask,
            terminal,
        )

    def scaled_dnbr(
        self,
        dnbr: RasterInput,
        mask: Optional[RasterInput] = None,
        *,
        terminal: bool = False,
        omitnan: bool = False,
    ) -> BasinValues:
        """
        scaled_dnbr  Computes mean catchment dNBR / 1000 for basins
        ----------
        self.scaled_dnbr(dnbr)
        Computes mean catchment dNBR for each stream segment in the network.
        These mean dNBR values are then divided by 1000 to place dNBR values
        roughly on the interval from 0 to 1. Returns the scaled dNBR values as a
        numpy 1D array. If a basin contains NaN or NoData values, then its dNBR
        value is set to NaN.

        self.scaled_dnbr(dnbr, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute scaled dNBR values. False elements are ignored. If a
        catchment only contains False elements, then its scaled dNBR value is set
        to NaN.

        self.scaled_dnbr(..., *, omitnan=True)
        Ignores NaN and NoData values when computing scaled dNBR values. However,
        if a basin only contains these values, then its scaled dNBR value will
        still be NaN.

        self.scaled_dnbr(..., *, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            dnbr: A dNBR raster for the watershed
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute scaled dNBR
            omitnan: True to ignore NaN and NoData values. If False (default),
                any basin with (unmasked) NaN or NoData values will have its value
                set to NaN.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean catchment dNBR/1000 for the basins
        """

        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        dnbr = self.basin_summary(method, dnbr, mask, terminal)
        return dnbr / 1000

    def scaled_thickness(
        self,
        soil_thickness: RasterInput,
        mask: Optional[RasterInput] = None,
        *,
        omitnan: bool = False,
        terminal: bool = False,
    ) -> BasinValues:
        """
        scaled_thickness  Computes mean catchment soil thickness / 100 for basins
        ----------
        self.scaled_thickness(soil_thickness)
        Computes mean catchment soil-thickness for each segment in the network.
        Then divides these values by 100 to place soil thicknesses approximately
        on the interval from 0 to 1. Returns a numpy 1D array with the scaled soil
        thickness values for each segment. Note that the soil thickness raster
        must have all positive values.

        self.scaled_thickness(soil_thickness, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean soil thicknesses. False elements are ignored. If
        a catchment only contains False elements, then its scaled soil thickness
        is set to NaN.

        self.scaled_thickness(..., *, omitnan=True)
        Ignores NaN and NoData values when computing scaled soil thickness values.
        However, if a basin only contains NaN and NoData, then its scaled soil
        thickness will still be NaN.

        self.scaled_thickness(..., *, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            soil_thickess: A raster with soil thickness values for the watershed.
                Cannot contain negative values.
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute scaled soil thicknesses
            omitnan: True to ignore NaN and NoData values. If False (default),
                any basin with (unmasked) NaN or NoData values will have its value
                set to NaN.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean catchment soil thickness / 100 for each basin
        """

        # Validate
        soil_thickness = self._validate(soil_thickness, "soil_thickness")
        validate.positive(
            soil_thickness.values, "soil_thickness", ignore=[soil_thickness.nodata, nan]
        )

        # Summarize
        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        soil_thickness = self.basin_summary(method, soil_thickness, mask, terminal)
        return soil_thickness / 100

    def sine_theta(
        self,
        sine_thetas,
        mask: Optional[RasterInput] = None,
        *,
        omitnan: bool = False,
        terminal: bool = False,
    ) -> BasinValues:
        """
        sine_theta  Computes the mean sin(theta) value for each segment's catchment
        ----------
        self.sine_theta(sine_thetas)
        Given a raster of watershed sin(theta) values, computes the mean sin(theta)
        value for each stream segment catchment. Here, theta is the slope angle. Note
        that the pfdf.utils.slope module provides utilities for converting from
        slope gradients (rise/run) to other slope measurements, including
        sin(theta) values. All sin(theta) values should be on the interval from
        0 to 1. Returns a numpy 1D array with the sin(theta) values for each segment.

        self.sine_theta(sine_thetas, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean sin(theta) values. False elements are ignored.
        If a catchment only contains False elements, then its sin(theta) value
        is set to NaN.

        self.sine_theta(..., *, omitnan=True)
        Ignores NaN and NoData values when computing mean sine theta values.
        However, if a basin only contains NaN and NoData, then its sine theta
        value will still be NaN.

        self.sine_theta(..., terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            sine_thetas: A raster of sin(theta) values for the watershed
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute sin(theta) values
            omitnan: True to ignore NaN and NoData values. If False (default),
                any basin with (unmasked) NaN or NoData values will have its value
                set to NaN.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean sin(theta) value for each basin
        """

        # Validate
        sine_thetas = self._validate(sine_thetas, "sine_thetas")
        validate.inrange(
            sine_thetas.values,
            sine_thetas.name,
            min=0,
            max=1,
            ignore=[sine_thetas.nodata, nan],
        )

        # Summarize
        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        return self.basin_summary(method, sine_thetas, mask, terminal)

    def slope(
        self, slopes: RasterInput, *, terminal: bool = False, omitnan: bool = False
    ) -> SegmentValues:
        """
        slope  Returns the mean slope (rise/run) for each segment
        ----------
        self.slope(slopes)
        self.slope(..., *, terminal=True)
        Given a raster of slopes (rise/run), returns the mean slope for each
        segment as a numpy 1D array. If a stream segment's pixels contain NaN or
        NoData values, then the slope for the segment is set to NaN. If terminal=True,
        only returns values for the terminal segments.

        self.slope(..., *, omitnan=True)
        Ignores NaN and NoData values when computing mean slope. However, if a
        segment only contains NaN and NoData values, then its value will still
        be NaN.
        ----------
        Inputs:
            slopes: A slope (rise/run) raster for the watershed
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            numpy 1D array: The mean slopes for the segments.
        """
        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        slopes = self.summary(method, slopes)
        if terminal:
            slopes = slopes[self.isterminal()]
        return slopes

    def relief(self, relief: RasterInput, terminal: bool = False) -> SegmentValues:
        """
        relief  Returns the vertical relief for each segment
        ----------
        self.relief(relief)
        self.relief(relief, terminal=True)
        Returns the vertical relief between each stream segment's outlet and the
        nearest ridge cell as a numpy 1D array. If terminal=True, only returns
        values for the terminal segments.
        ----------
        Inputs:
            relief: A vertical relief raster for the watershed
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            numpy 1D array: The vertical relief for each segment
        """

        relief = self._validate(relief, "relief")
        relief = self._values_at_outlets(relief)
        if terminal:
            relief = relief[self.isterminal()]
        return relief

    def ruggedness(
        self,
        relief: RasterInput,
        relief_per_m: Optional[scalar] = None,
        terminal: bool = False,
    ) -> SegmentValues:
        """
        ruggedness  Returns the ruggedness of each stream segment catchment
        ----------
        self.ruggedness(relief)
        self.ruggedness(relief, relief_per_m)
        Returns the ruggedness of the catchment for each stream segment in the
        network. Ruggedness is defined as a stream segment's vertical relief,
        divided by the square root of its catchment area. By default, relief
        values should be in meters. If this is not the case, use the "relief_per_m"
        option to provide a conversion factor between relief units and meters.
        This ensures that ruggedness values are scaled correctly.

        self.ruggedness(..., terminal=True)
        Only returns values for the terminal segments.
        ----------
        Inputs:
            relief: A vertical relief raster for the watershed
            base_unit: True to interpret reliefs in the base unit of the CRS.
                False (default) to interpret reliefs in meters instead.
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            numpy 1D array: The topographic ruggedness of each stream segment
        """

        relief_per_m = validate.conversion(relief_per_m, "relief_per_m")
        area = self.area(terminal=terminal) * 1e6
        relief = self.relief(relief, terminal=terminal)
        if relief_per_m is not None:
            relief = relief / relief_per_m
        return relief / np.sqrt(area)

    def upslope_ratio(self, mask: RasterInput, terminal: bool = False) -> BasinValues:
        """
        upslope_ratio  Returns the proportion of basin pixels that meet a criteria
        ----------
        self.upslope_ratio(mask)
        Given a raster mask, computes the proportion of True pixels in the
        catchment basin for each stream segment. Returns the ratios as a numpy 1D
        array with one element per stream segment. Ratios will be on the interval
        from 0 to 1. Note that NoData pixels in the mask are interpreted as False.

        self.upslope_ratio(mask, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            mask: A raster mask for the watershed. The method will compute the
                proportion of True elements in each catchment
            terminal: True to only compute values for the terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The proportion of True values in each basin
        """
        counts = self._accumulation(mask=mask, terminal=terminal)
        npixels = self._basin_npixels(terminal)
        return counts / npixels

    #####
    # Filtering
    #####

    def _validate_selection(self, ids: Any, indices: Any) -> SegmentIndices:
        "Validates IDs and/or logical indices and returns them as logical indices"

        # Default or validate logical indices
        if indices is None:
            indices = np.zeros(self.size, bool)
        else:
            indices = validate.vector(indices, "indices", dtype=real, length=self.size)
            indices = validate.boolean(indices, "indices")

        # Default or validate IDs.
        if ids is None:
            ids = np.zeros(self.size, bool)
        else:
            ids = validate.vector(ids, "ids", dtype=real)
            self._check_ids(ids, "ids")

            # Convert IDs to logical indices. Return union of IDs and indices
            ids = np.isin(self._ids, ids)
        return ids | indices

    @staticmethod
    def _removable(
        requested: SegmentIndices,
        child: SegmentValues,
        parents: SegmentParents,
        upstream: bool,
        downstream: bool,
    ) -> SegmentIndices:
        "Returns the indices of requested segments on the edges of their local networks"

        edge = False
        if downstream:
            edge = edge | (child == -1)
        if upstream:
            edge = edge | (parents == -1).all(axis=1)
        return requested & edge

    def continuous(
        self,
        *,
        ids: Optional[vector] = None,
        indices: Optional[SegmentIndices] = None,
        keep: bool = False,
        upstream: bool = True,
        downstream: bool = True,
    ) -> SegmentIndices:
        """
        Indicates segments that can be removed while preserving flow continuity
        ----------
        self.continuous(ids)
        self.continuous(indices)
        Given a set of segments slated for removal from the network, returns the
        indices of segments that can be removed while preserving flow continuity.
        An segment slated for removal will be retained if it is between two
        segments being retained. Equivalently, segments are only removed from the
        upstream and downstream ends of their local drainage networks. Conceptually,
        the algorithm first marches upstream, and removes segments until it reaches
        a segment that was not indicated as input. The algorithm then marches
        downstream, again removing segments until reaching a segment not indicated
        as input.

        Returns the indices of the segments that can be removed from the network.
        This is a boolean numpy 1D array with one element per segment. True elements
        indicate segments that were both (1) indicated as input, and (2) can be
        removed without disrupting flow continuity.

        self.continuous(..., keep=True)
        Indicates that the input segments represent segments that should be retained
        in the network, rather than being removed. The output array is still a
        boolean 1D array with one element per segment. However, True elements
        indicate segments that either (1) were indicated as input, or (2) should
        be retained to preserve flow continuity.

        In general, use keep=True when you intend to filter the network using the
        "keep" command. Use the default keep=False when you intend to filter the
        network using the "remove" comand.

        self.continuous(..., upstream=False)
        self.continuous(..., downstream=False)
        Further customizes the flow continuity algorithm. When upstream=False,
        the algorithm will not remove segments on the upstream end of a local
        drainage network. When downstream=False, the algorithm will not remove
        segments on the downstream end of a local drainage network.
        ----------
        Inputs:
            ids: The IDs of segments that should be removed/retained in the network.
            indices: A boolean numpy array with one element per stream segment.
                If keep=False (default), True elements indicate segments slated
                for removal from the network. If keep=True, True elements indicate
                segments that should be retained in the network.
            keep: True if the input segments should be retained in the network.
                False (default) if the input segments are slated for removal.
            upstream: Set to False to prevent segments from being removed from
                the upstream ends of local drainage networks.
            downstream: Set to False to prevent segments from being removed from
                the downstream ends of local drainage networks.

        Outputs:
            boolean numpy 1D array: The indices of segments that can be
                removed/retained in the network while preserving flow continuity.
                If keep=False (default), True elements indicate segments that can
                be removed. If keep=True, True elements indicate segments that
                should be retained.
        """

        # Get the segments requested for removal
        requested = self._validate_selection(ids, indices)
        if keep:
            requested = ~requested

        # Initialize segments actually being removed. Get working copies of
        # parent-child relationships.
        remove = np.zeros(self.size, bool)
        child = self._child.copy()
        parents = self._parents.copy()

        # Iteratively select requested segments on the edges of their local networks.
        # Update child-parent segments and repeat for new edge segments
        removable = self._removable(requested, child, parents, upstream, downstream)
        while np.any(removable):
            remove[removable] = True
            requested[removable] = False
            self._update_family(child, parents, removable)
            removable = self._removable(requested, child, parents, upstream, downstream)

        # Return keep/remove indices as appropriate
        if keep:
            return ~remove
        else:
            return remove

    def remove(
        self, *, ids: Optional[vector] = None, indices: Optional[SegmentIndices] = None
    ) -> None:
        """
        remove  Removes segments from the network
        ----------
        self.remove(*, ids)
        self.remove(*, indices)
        Removes the indicated segments from the network. If using "ids", the
        input should be a list or numpy 1D array whose elements are the IDs of
        the segments that should be removed from the network. If using "indices"
        the input should be a boolean numpy 1D array with one element per segment
        in the network. True elements indicate the stream segments that should be
        removed. False elements will be retained. If you provide both inputs,
        segments indicated by either input are removed from the network.

        Note that removing terminal outlet segments will cause any previously located
        basins to be deleted. As such we recommend calling the "locate_basins"
        command after this command.
        ----------
        Inputs:
            ids: A list or numpy 1D array listing the IDs of segments that should
                be removed from the network
            indices: A boolean numpy 1D array with one element per stream segment.
                True elements indicate segments that should be removed from the
                network.
        """

        # Validate. Get segments being kept / removed
        remove = self._validate_selection(ids, indices)
        keep = ~remove

        # Compute new attributes
        segments, indices = self._update_segments(remove)
        ids = self.ids[keep]
        npixels = self.npixels[keep]
        child, parents = self._update_connectivity(remove)
        basins = self._update_basins(remove)

        # Update object
        self._segments = segments
        self._ids = ids
        self._indices = indices
        self._npixels = npixels
        self._child = child
        self._parents = parents
        self._basins = basins

    def keep(
        self,
        *,
        ids: Optional[vector] = None,
        indices: Optional[SegmentIndices] = None,
    ) -> None:
        """
        keep  Restricts the network to the indicated segments
        ----------
        self.keep(*, ids)
        self.keep(*, indices)
        Restricts the network to the indicated segments, discarding all other
        segments. If using "ids", the input should be a list or numpy 1D array whose
        elements are the IDs of the segments to retain in the network. If using
        "indices" the input should be a boolean numpy 1D array with one element
        per segment in the network. True elements indicate stream segments that
        should be retained. False elements will be removed. If you provide both
        inputs, segments indicated by either input are retained in the network.

        Note that discarding terminal outlet segments will cause any previously
        located basins to be deleted. As such, we recommend calling "locate_basins"
        after this command.
        ----------
        Inputs:
            ids: A list or numpy 1D array listing the IDs of segments that should
                be retained in the network
            indices: A boolean numpy 1D array with one element per stream segment.
                True elements indicate segments that should be retained in the network.
        """

        keep = self._validate_selection(ids, indices)
        self.remove(indices=~keep)

    def copy(self) -> Self:
        """
        copy  Returns a copy of a Segments object
        ----------
        self.copy()
        Returns a copy of the current Segments object. Stream segments can be
        removed from the new/old objects without affecting one another. Note that
        the flow direction raster and saved basin rasters are not duplicated in
        memory. Instead, both objects reference the same underlying array.
        ----------
        Outputs:
            Segments: A copy of the current Segments object.
        """

        copy = super().__new__(Segments)
        copy._flow = self._flow
        copy._segments = self._segments.copy()
        copy._ids = self._ids.copy()
        copy._indices = self._indices.copy()
        copy._npixels = self._npixels.copy()
        copy._child = self._child.copy()
        copy._parents = self._parents.copy()
        copy._basins = None
        copy._basins = self._basins
        return copy

    #####
    # Filtering Updates
    #####

    def _update_segments(
        self, remove: SegmentIndices
    ) -> tuple[list[shapely.LineString], indices]:
        "Computes updated linestrings and pixel indices after segments are removed"

        # Initialize new attributes
        segments = self.segments
        indices = self.indices

        # Delete items from lists
        (removed,) = np.nonzero(remove)
        for k in reversed(removed):
            del segments[k]
            del indices[k]
        return segments, indices

    @staticmethod
    def _update_family(
        child: SegmentValues, parents: SegmentParents, remove: SegmentIndices
    ) -> None:
        "Updates child-parent relationships in-place after segments are removed"

        indices = np.nonzero(remove)
        removed = np.isin(child, indices)
        child[removed] = -1
        removed = np.isin(parents, indices)
        parents[removed] = -1

    @staticmethod
    def _update_indices(family: RealArray, nremoved: VectorArray) -> None:
        "Updates connectivity indices in-place after segments are removed"

        adjust = family != -1
        indices = family[adjust]
        family[adjust] = indices - nremoved[indices]

    def _update_connectivity(
        self, remove: SegmentIndices
    ) -> tuple[SegmentValues, SegmentParents]:
        "Computes updated child and parents after segments are removed"

        # Initialize new attributes
        child = self._child.copy()
        parents = self._parents.copy()

        # Limit arrays to retained segments
        keep = ~remove
        child = child[keep]
        parents = parents[keep]

        # Update connectivity relationships and reindex as necessary
        self._update_family(child, parents, remove)
        nremoved = np.cumsum(remove)
        self._update_indices(child, nremoved)
        self._update_indices(parents, nremoved)
        return child, parents

    def _update_basins(self, remove: SegmentIndices) -> MatrixArray | None:
        "Resets basins if any terminal basin outlets were removed"

        # If there aren't any basins, just leave them as None
        if self._basins is None:
            return None

        # Get the ids of the removed segments. Reset if any of the removed IDs
        # are in the raster. Otherwise, retain the old raster
        ids = self.ids[remove]
        if np.any(np.isin(ids, self._basins)):
            return None
        else:
            return self._basins

    #####
    # Export
    #####

    def _validate_properties(
        self,
        properties: Any,
        terminal: bool,
    ) -> tuple[PropertyDict, PropertySchema]:
        "Validates a GeoJSON property dict for export"

        # Initialize the final property dict and schema. Properties are optional,
        # so justuse an empty dict if there are none
        final = {}
        schema = {}
        if properties is None:
            properties = {}

        # Get the allowed lengths and the required final length
        length = self._nbasins(terminal)
        allowed = [self.size]
        if terminal:
            allowed.append(self.nlocal)

        # Require a dict with string keys
        dtypes = real + [str]
        validate.type(properties, "properties", dict, "dict")
        for k, key in enumerate(properties.keys()):
            validate.type(key, f"properties key {k}", str, "string")

            # Values must be numpy 1D arrays with either one element per segment,
            # or one element per exported feature
            name = f"properties['{key}']"
            vector = validate.vector(properties[key], name, dtype=dtypes)
            if vector.size not in allowed:
                allowed = " or ".join([str(length) for length in allowed])
                raise ShapeError(
                    f"{name} must have {allowed} elements, but it has "
                    f"{vector.size} elements instead."
                )

            # Extract terminal properties as needed
            if vector.size != length:
                vector = vector[self.isterminal()]

            # Convert boolean to int
            if vector.dtype == bool:
                vector = vector.astype("int")
                schema[key] = "int"

            # If a string, parse the width from the vector dtype
            elif vector.dtype.char == "U":
                dtype = str(vector.dtype)
                k = dtype.find("U")
                width = int(dtype[k + 1 :])
                schema[key] = f"str:{width}"

            # Convert int and float precisions to built-in
            elif np.issubdtype(vector.dtype, np.integer):
                vector = vector.astype(int, copy=False)
                schema[key] = "int"
            elif np.issubdtype(vector.dtype, np.floating):
                vector = vector.astype(float, copy=False)
                schema[key] = "float"

            # Record the final vector and return with the schema
            final[key] = vector
        return final, schema

    def _validate_export(
        self, properties: Any, type: Any
    ) -> tuple[FeatureType, PropertyDict, PropertySchema]:
        "Validates export type and properties"

        type = validate.option(
            type, "type", allowed=["segments", "segment outlets", "outlets", "basins"]
        )
        terminal = "segment" not in type
        properties, schema = self._validate_properties(properties, terminal)
        return type, properties, schema

    def _basin_polygons(self):
        "Returns a generator of drainage basin (Polygon, ID value) tuples"

        basins = self._locate_basins()
        mask = basins.astype(bool)
        return rasterio.features.shapes(
            basins, mask, connectivity=8, transform=self.transform.affine
        )

    def _geojson(
        self,
        properties: PropertyDict | None,
        type: FeatureType,
    ) -> tuple[FeatureCollection, PropertySchema]:
        "Builds geojson.FeatureCollection and property schema"

        # Validate
        type, properties, schema = self._validate_export(properties, type)

        # Basins are derived from rasterio shapes. Also track basin IDs.
        # (Basin geometries are unordered, so need to track which property is which)
        if type == "basins":
            geometries = self._basin_polygons()
            ids = self.terminal_ids

        # Everything else is derived from the shapely linestrings
        elif type == "outlets":
            geometries = [
                segment
                for keep, segment in zip(self.isterminal(), self._segments)
                if keep
            ]
        else:
            geometries = self._segments

        # Build each feature and group them into a FeatureCollection. Start by
        # getting a geojson-like geometry for each feature
        features = []
        for g, geometry in enumerate(geometries):
            if "outlets" in type:
                outlet = geometry.coords[-1]
                geometry = geojson.Point(outlet)
            elif type == "segments":
                geometry = geojson.LineString(geometry.coords)

            # For basins, get the property index in addition to the geometry
            else:
                id = geometry[1]
                geometry = geometry[0]
                index = np.argwhere(id == ids)
                g = int(index[0, 0])

            # Get the data properties for each feature as built-in types
            builtins = {"float": float, "int": int, "str": str}
            data = {}
            for field, vector in properties.items():
                value = vector[g]
                dtype = schema[field].split(":")[0]
                convert = builtins[dtype]
                data[field] = convert(value)

            # Build feature and add to collection
            feature = Feature(geometry=geometry, properties=data)
            features.append(feature)
        return FeatureCollection(features), schema

    def geojson(
        self,
        properties: Optional[PropertyDict] = None,
        *,
        type: FeatureType = "segments",
    ) -> FeatureCollection:
        """
        geosjon  Exports the network to a geojson.FeatureCollection object
        ----------
        self.geojson()
        self.geojson(..., *, type='segments')
        Exports the network to a geojson.FeatureCollection object. The individual
        Features have LineString geometries whose coordinates proceed from upstream
        to downstream. Will have one feature per stream segment.

        self.geojson(..., *, type='basins')
        Exports terminal outlet basins as a collection of Polygon features. The
        number of features will be <= the number of local drainage networks.
        (The number of features will be < the number of local networks if a local
        network flows into another local network).

        Note that you can use Segments.locate_basins to pre-locate the basins
        before calling this command. If not pre-located, then this command will
        locate the basins sequentially, which may take a while. Note that the
        "locate_basins" command includes options to parallelize this process,
        which may improve runtime.

        self.geojson(..., *, type='outlets')
        self.geojson(..., *, type='segment outlets')
        Exports outlet points as a collection of Point features. If type="outlets",
        exports the terminal outlet points, which will have one feature per local
        drainage network. If type="segment outlets", exports the complete set of
        outlet points, which will have one feature per segment in the network.

        self.geojson(properties, ...)
        Specifies data properties for the GeoJSON features. The "properties" input
        should be a dict. Each key should be a string and will be interpreted as
        the name of the associated property field. Each value should be a numpy
        1D array with an integer, floating, or boolean dtype. All properties in
        the output GeoJSON features will have a floating dtype, regardless of the
        input type. If exporting segments or segment outlets, then each array
        should have one element per segment in the network. If exporting basins or
        outlets, then each array should have one element per local drainage network.
        ----------
        Inputs:
            properties: A dict whose keys are the (string) names of the property
                fields. Each value should be a numpy 1D array with an integer,
                floating-point, or boolean dtype. Each array should have one element
                per segment (for segments or segment outlets), or one element
                per local drainage network (for outlets or basins).
            type: A string indicating the type of feature to export. Options are
                "segments", "basins", "outlets", or "segment outlets"

        Outputs:
            geojson.FeatureCollection: The collection of stream network features
        """

        return self._geojson(properties, type)[0]

    def save(
        self,
        path: Pathlike,
        properties: Optional[PropertyDict] = None,
        *,
        type: FeatureType = "segments",
        driver: Optional[str] = None,
        overwrite: bool = False,
    ) -> None:
        """
        save  Saves the network to a vector feature file
        ----------
        save(path)
        save(path, *, type='segments')
        save(..., overwrite=True)
        Saves the network to the indicated path. Each segment is saved as a vector
        feature with a LineString geometry whose coordinates proceed from upstream
        to downstream. The vector features will not have any data properties. In
        the default state, the method will raise a FileExistsError if the file
        already exists. Set overwrite=True to enable the replacement of existing
        files.

        By default, the method will attempt to guess the intended file format based
        on the path extensions, and will raise an Exception if the file format
        cannot be guessed. However, see below for a syntax to specify the driver,
        regardless of extension. You can use:
            >>> pfdf.utils.driver.extensions('vector')
        to return a summary of supported file format drivers, and their associated
        extensions.

        self.save(..., *, type='basins')
        Saves the terminal outlet basins as a collection of Polygon features.
        The number of features will be <= the number of local drainage networks.
        (The number of features will be < the number of local networks if a local
        network flows into another local network).

        Note that you can use Segments.locate_basins to pre-locate the basins
        before calling this command. If not pre-located, then this command will
        locate the basins sequentially, which may take a while. Note that the
        "locate_basins" command includes options to parallelize this process,
        which may improve runtime.

        self.save(..., *, type='outlets')
        self.save(..., *, type='segment outlets')
        Saves outlet points as a collection of Point features. If type="outlets",
        saves the terminal outlet points, which will have one feature per local
        drainage network. If type="segment outlets", saves the complete set of
        outlet points, which will have one feature per segment in the network.

        self.save(path, properties, ...)
        Specifies data properties for the saved features. The "properties" input
        should be a dict. Each key should be a string and will be interpreted as
        the name of the associated property field. Each value should be a numpy
        1D array with an integer, floating, or boolean dtype. All properties in
        the saved features will have a floating dtype, regardless of the input
        type. If saving segments or segment outlets, then each array should have
        one element per segment in the network. If saving basins or outlets,
        then each array should have one element per local drainage network.

        save(..., *, driver)
        Specifies the file format driver to used to write the vector feature file.
        Uses this format regardless of the file extension. You can call:
            >>> pfdf.utils.driver.vectors()
        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR)
        to write vector files, and so additional drivers may work if their
        associated build requirements are met. You can call:
            >>> fiona.drvsupport.vector_driver_extensions()
        to summarize the drivers currently supported by fiona, and a complete
        list of driver build requirements is available here:
        https://gdal.org/drivers/vector/index.html
        ----------
        Inputs:
            path: The path to the output file
            properties: A dict whose keys are the (string) names of the property
                fields. Each value should be a numpy 1D array with an integer,
                floating-point, or boolean dtype. Each array should have one element
                per segment (for segments or segment outlets), or one element
                per local drainage network (for outlets or basins).
            type: A string indicating the type of feature to export. Options are
                "segments", "basins", "outlets", or "segment outlets"
            overwrite: True to allow replacement of existing files. False (default)
                to prevent overwriting.
            driver: The name of the file-format driver to use when writing the
                vector feature file. Uses this driver regardless of file extension.
        """

        # Validate and get features as geojson
        validate.output_path(path, overwrite)
        collection, property_schema = self._geojson(properties, type)

        # Build the schema
        geometries = {
            "segments": "LineString",
            "basins": "Polygon",
            "outlets": "Point",
            "segment outlets": "Point",
        }
        schema = {
            "geometry": geometries[type],
            "properties": property_schema,
        }

        # Write file
        records = collection["features"]
        with fiona.open(path, "w", driver=driver, crs=self.crs, schema=schema) as file:
            file.writerecords(records)
