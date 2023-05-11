"""
staley2017  Implements the logistic models presented in Staley et al., 2017
"""

import numpy as np
from abc import ABC, abstractmethod
from dhfa import validate
from dhfa.utils import real
from dfha.segments import Segments
from typing import NoReturn, Dict
from nptyping import NDArray, Shape, Boolean
from dfha.typing import Raster, SegmentValues, VectorArray, Durations, DurationValues

# Type aliases
ParameterDict = Dict[str, DurationValues]
VariableDict = Dict[str, SegmentValues]


#####
# Logistic model solver
#####


#####
# Variables
#####


def burn_gradient(
    segments: Segments, flow_directions: Raster, gradient: Raster, isburned: Raster
):
    """
    burn_gradient  Returns the mean gradient of upslope pixels burned at a given severity
    ----------
    burn_gradient(segments, flow_directions, gradients, isburned)
    Computes the mean gradient of upslope pixels burned at a given severity for
    each stream segment. Returns a numpy 1D array with the gradient for each segment.
    ----------
    Inputs:
        segments: A set of stream segments
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels. Must have the same shape as the raster used to derive
            the stream segments.
        gradients: A raster holding the gradients - sin(theta) - for the DEM
            pixels. Must have the same shape as the raster use to derive the
            stream segments.
        isburned: A raster indicating the DEM pixels that are burned at the
            desired severity level. Pixels meeting the criteria should have a
            value of 1. All other pixels should be 0. Must have the same shape
            as the raster used to derive the stream segments.

    Outputs:
        numpy 1D array: The mean gradients for the stream segments.
    """

    return segments.masked_catchment_mean(flow_directions, gradient, isburned)


def _kf_factor(*args, **kwargs):
    """This function is just an alias to kf_factor. It exists so that users can
    use kf_factor to refer to variables in functions that also call the
    kf_factor function."""
    return kf_factor(*args, **kwargs)


def kf_factor(segments, npixels, flow_directions, kf_factor):
    """
    kf_factor  Returns the mean KF-Factor for a set of stream segment catchments
    ----------
    kf_factor(segments, npixels, flow_directions, kf_factor)
    Computes the mean KF-factors for a set of stream segments. Mean KF-factor is
    calculated over the full catchment area of each stream segment.
    ----------
    Inputs:
        segments: A set of stream segments
        npixels: The number of upslope pixels for each stream segment
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels. Must have the same shape as the raster used to derive
            the stream segments.
        kf_factor: A raster holding KF-factor values for the DEM pixels. Must have
            the same shape as the raster used to derive the stream segments.

    Outputs:
        numpy 1D array: The mean KF-factor for each stream segment.
    """
    return segments.catchment_mean(npixels, flow_directions, kf_factor)


def ruggedness(
    segments: Segments, segment_areas: SegmentValues, relief: Raster
) -> SegmentValues:
    """
    ruggedness  Computes topographic ruggedness for a set of stream segments
    ----------
    ruggedness(segments, segment_areas, relief)
    Computes topographic ruggedness for a set of stream segments. Ruggedness
    is calculated via:

        Ruggedness = vertical relief / sqrt(upslope area)

    Returns the ruggedness values as a numpy 1D array.
    ----------
    Inputs:
        segments: A set of stream segments
        segment_areas: The total upslope area of each stream segment (as determined
            for the most downstream pixel). All values must be positive.
        relief: A raster holding the vertical relief of the DEM pixels. (See
            the "dem.relief" function to calculate this raster). Must have the
            same shape as the raster used to derive the stream segments.

    Outputs:
        numpy 1D array: The ruggedness of each stream segment.
    """
    validate.vector(segment_areas, "segment_areas", dtype=real, length=len(segments))
    validate.positive(segment_areas, "segment_areas")
    relief = segments.summary("max", relief)
    return relief / np.sqrt(segment_areas)


def scaled_dnbr(
    segments: Segments, npixels: SegmentValues, flow_directions: Raster, dNBR: Raster
) -> SegmentValues:
    """
    scaled_dnbr  Computes mean dNBR/1000 for a set of stream segment catchments
    ----------
    scaled_dnbr(segments, npixels, flow_directions, dNBR)
    Computes mean scaled dNBR for a set of stream segments. Mean dNBR is calculated
    over the full catchment area of each stream segment. This value is then scaled
    by 1000 to place the final value roughly on an interval from 0 to 1.
    ----------
    Inputs:
        segments: A set of stream segments
        npixels: The number of upslope pixels for each stream segment.
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels. Must have the same shape as the raster used to derive
            the stream segments.
        dNBR: A raster holding dNBR values for the DEM pixels. Must have the same
            shape as the raster used to derive the stream segments.

    Outputs:
        numpy 1D array: The scaled dNBR values for the stream segments
    """
    dNBR = segments.catchment_mean(npixels, flow_directions, dNBR)
    return dNBR / 1000


def scaled_thickness(segments, npixels, flow_directions, soil_thickness):
    """
    scaled_thickness  Returns mean soil thickness / 100 for a set of stream segments
    ----------
    scaled_thickness(segments, npixels, flow_directions, soil_thickness)
    Computes mean scaled soil thickness for a set of stream segments. Mean soil
    thickness is computed over the full catchment area of each stream segment.
    These values are then scaled by 100 to place them roughly on the interval
    from 0 to 1.
    ----------
    Inputs:
        segments: A set of stream segments
        npixels: The number of upslope pixels for each stream segment
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels. Must have the same shape as the raster used to derive
            the stream segments.
        soil_thickness: A raster holding the soil thickness for the DEM pixels.
            Must have the same shape as the raster used to derive the stream segments.

    Outputs:
        numpy 1D array: The mean scaled soil thickness for each stream segment
    """
    thickness = segments.catchment_mean(npixels, flow_directions, soil_thickness)
    return thickness / 100


def upslope_ratio(
    segments: Segments,
    npixels: SegmentValues,
    flow_directions: Raster,
    meets_criteria: Raster,
) -> SegmentValues:
    """
    upslope_ratio  Computes the proportion of upslope pixels that meet some criteria
    ----------
    upslope_ratio(segments, npixels, flow_directions, meets_criteria)
    Computes the proportion of upslope pixels that meet a criterion. This function
    is generalizable to a number of model variables. The "meets_criteria" input
    is a raster indicating which DEM pixels meet the desired criteria. Pixels
    meeting the criteria should have a value of 1. All others should be 0.

    Note that this function is generalizable to a number of model variables.
    For example it can be used to compute:

        M1, T: The proportion of upslope pixels burned at high-or-moderate severity
               with slopes greater than 23 degrees.
        M3, F: The proportion of upslope pixels burned at high-or-moderate severity
        M4, T: The proportion of upslope pixels burned at low-moderate-high severity
               with slopes greater than 30 degrees.
    ----------
    Inputs:
        segments: A set of stream segments
        npixels: The number of upslope pixels for each stream segment.
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels. Must have the same shape as the raster used to derive
            the stream segments.
        meets_criteria: A raster indicating which DEM pixels meet the desired
            criteria. Must have the same shape as the raster used to derive the
            stream segments.

    Outputs:
        numpy 1D array: The burn ratio for each stream segment
    """
    return segments.catchment_mean(npixels, flow_directions, meets_criteria)


#####
# Model classes
#####


class Model(ABC):
    """
    Model  An abstract base class for the 4 logistic models from Staley et al., 2017
    ----------
    The class provides an interface for some of the common patterns between the
    the 4 logistic models. It defines the rainfall durations used to calibrate
    parameters, and provides a function to query model parameters for a given
    set of durations. The class also requires each concrete model to define a
    "variables" function that calculates the (T)errain, (F)ire, and (S)oil
    variables required to run the model.
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters

    Abstract Properties:
        B               - Logistic Model intercepts
        Ct              - Coefficients for the (t)errain variable
        Cf              - Coefficients for the (f)ire variable
        Cs              - Coefficients for the (s)oil variable

    Methods:
        parameters      - Returns the model parameters for a queried set of durations

    Abstract Methods:
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments

    Utilities:
        _variable_dict  - Returns a dict holding terrain, fire, and soil variables

    Exceptions:
        DurationsError  - When a queried duration is not a valid duration
    """

    # The rainfall durations used to calibrate model parameters
    durations = [15, 30, 60]

    # Model parameters: Each concrete model should define these. Each property
    # should have 3 elements and follow the order of the above durations
    B = None  # Logistic model intercepts
    Ct = None  # Terrain coefficients
    Cf = None  # Fire coefficients
    Cs = None  # Soil coefficients

    @classmethod
    def DurationsError(
        cls, durations: VectorArray, valid: NDArray[Shape["Durations"], Boolean]
    ) -> NoReturn:
        """An exception for invalid rainfall durations. Notes the invalid duration
        in the error message and informs the user of valid values."""
        bad = np.argwhere(valid == 0)[0]
        allowed = ", ".join([str(value) for value in cls.durations])
        return ValueError(
            f"Duration {bad} ({durations[bad]}) is not an allowed value. Allowed values are: {allowed}"
        )

    @classmethod
    def parameters(cls, durations: Durations = durations) -> ParameterDict:
        """
        parameters  Return model parameters for the queried durations.
        ----------
        Model.parameters()
        Returns a dict with the logistic model intercepts (B), terrain coefficients (Ct),
        fire coefficients (Cf), and soil coefficients (Cs) for a model. Each
        value in the dict is a numpy 1D array with 3 elements. The three elements
        are for 15-minute, 30-minute, and 60-minute rainfall durations (in that order).

        Model.parameters(durations)
        Returns values for the queried rainfall durations. Each value in the dict
        will have one element per queried duration, in the same order as the queries.
        Valid durations to query are 15, 30, and 60.
        ----------
        Inputs:
            durations: A list of rainfall durations for which to return model parameters

        Outputs:
            Dict[str, numpy 1D array]: The queried coefficients for the model.
                'B': Logistic model intercepts
                'Ct': Terrain coefficients
                'Cf': Fire coefficients
                'Cs': Soil coefficients
        """
        # Validate durations
        durations = validate.vector(durations, "durations", real)
        valid = np.isin(durations, cls.durations)
        if not all(valid):
            raise cls.DurationsError(durations, valid)

        # Get duration indices
        indices = np.empty(durations.shape)
        for d, duration in enumerate(cls.durations):
            elements = np.argwhere(durations == duration)
            indices[elements] = d

        # Get parameters at the specified duration indices
        parameters = [cls.B, cls.Ct, cls.Cf, cls.Cs]
        names = ["B", "Ct", "Cf", "Cs"]
        return {
            name: np.array(values)[indices] for name, values in zip(names, parameters)
        }

    @staticmethod
    @abstractmethod
    def variables(segments: Segments, *args, **kwargs) -> VariableDict:
        """
        variables  Returns terrain, fire, and soil variables for a model
        ----------
        Model.variables(segments, ...)
        Given a set of stream segments, returns a dict with the terrain (T),
        fire (F), and soil (S) variables needed to run the model. Each value in
        the dict is a numpy 1D array with one element per stream segment.
        ----------
        Inputs:
            segments: A set of stream segments
            *args, **kwargs: These will vary by model.

        Outputs:
            Dict[str, numpy 1D array]: The variables needed to run the model
                for the stream segments.
                'T': The terrain variable for each stream segment
                'F': The fire variable for each stream segment
                'S': The soil variable for each stream segment
        """
        pass

    @staticmethod
    def _variable_dict(
        T: SegmentValues, F: SegmentValues, S: SegmentValues
    ) -> VariableDict:
        "Groups models variables into a dict"
        return {"T": T, "F": F, "S": S}


class M1(Model):
    """
    M1  Implements the M1 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

    Terrain: The proportion of upslope area with both high-or-moderate severity
        burn AND slopes greater than 23 degree.

    Fire: Mean catchment dNBR / 1000

    Soil: Mean catchment KF-factor
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic Model intercepts
        Ct              - Terrain coefficients
        Cf              - Fire coefficients
        Cs              - Soil coefficients

    Methods:
        parameters      - Returns model parameters for the queried rainfall durations
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments
    """

    # Model parameters
    B = [-3.63, -3.61, -3.21]
    Ct = [0.41, 0.26, 0.17]
    Cf = [0.67, 0.39, 0.20]
    Cs = [0.70, 0.50, 0.220]

    @staticmethod
    def variables(
        segments: Segments,
        npixels: SegmentValues,
        flow_directions: Raster,
        high_moderate_23: Raster,
        dNBR: Raster,
        kf_factor: Raster,
    ) -> VariableDict:
        """
        variables  Returns the M1 terrain, fire, and soil variables for a set of stream segments
        ----------
        M1.variables(segments, npixels, flow_directions,
                                              high_moderate_23, dNBR, kf_factor)
        Returns the terrain, fire, and soil variables required to run the M1 model
        for a set of stream segments. The terrain variable is the ratio of upslope
        pixels that have both moderate-or-high burn severity, and slopes greater
        than 23 degrees. The fire variable is mean catchment dNBR / 1000, and
        the soil variable is the mean catchment KF-factor. Returns a dict mapping
        each variable to a numpy 1D array with the values of the variable for the
        stream segments.
        ----------
        Inputs:
            segments: A set of stream segments
            npixels: The number of upslope pixels for each stream segment.
            flow_directions: A raster holding TauDEM-style D8 flow directions for the
                DEM pixels. Must have the same shape as the raster used to derive
                the stream segments.
            high_moderate_23: A raster indicating DEM pixels that have both
                high-or-moderate burn severity, and slopes >= 23 degrees. Pixels
                that meet this criteria should have a value of 1. All other pixels
                should be 0. Must have the same shape as the raster used to derive
                the stream segments.
            dNBR: A raster holding dNBR values for the DEM pixels. Must have the
                same shape as the raster used to derive the stream segments.
            kf_factor: A raster holding KF-factor values for the DEM pixels. Must
                have the same shape as the raster used to derive the stream segments.

        Output:
            Dict[str, numpy 1D array]: The values of the model variables for the
                input stream segments.
                'T': The proportion of upslope area burned at high-or-moderate
                    severity with slopes greater than 23 degrees.
                'F': Mean catchment dNBR / 1000
                'S': Mean catchment KF-factor
        """
        T = upslope_ratio(npixels, flow_directions, high_moderate_23)
        F = scaled_dnbr(segments, npixels, flow_directions, dNBR)
        S = _kf_factor(segments, npixels, flow_directions, kf_factor)
        return Model._variable_dict(T, F, S)


class M2(Model):
    """
    M2  Implements the M2 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

    Terrain: The mean gradient of upslope area burned with high-or-moderate severity

    Fire: Mean catchment dNBR / 1000

    Soil: Mean catchment KF-factor
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic model intercepts
        Ct              - Terrain coefficients
        Cf              - Fire coefficients
        Cs              - Soil coefficients

    Methods:
        parameters      - Returns model parameters for the queried rainfall durations
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments
    """

    # Model parameters
    B = [-3.62, -3.61, -3.22]
    Ct = [0.64, 0.42, 0.27]
    Cf = [0.65, 0.38, 0.19]
    Cs = [0.68, 0.49, 0.22]

    def variables(
        segments: Segments,
        npixels: SegmentValues,
        flow_directions: Raster,
        gradient: Raster,
        high_moderate: Raster,
        dNBR: Raster,
        kf_factor: Raster,
    ):
        """
        variables  Returns the M2 terrain, fire, and soil variables for a set of stream segments
        ----------
        M2.variables(segments, npixels, flow_directions,
                                        gradient, high_moderate, dNBR, kf_factor)
        Returns the terrain, fire, and soil variables required to run the M1 model
        for a set of stream segments. The terrain variable is the mean gradient of
        upslope pixels burned with high-or-moderate severity. The fire variable
        is mean catchment dNBR / 1000. The soil variable is mean catchment KF-factor.
        Returns a dict mapping each variable to a numpy 1D array with the values
        of the variable for the stream segments.
        ----------
        Inputs:
            segments: A set of stream segments
            npixels: The number of upslope pixels for each stream segment.
            flow_directions: A raster holding TauDEM-style D8 flow directions for the
                DEM pixels. Must have the same shape as the raster used to derive
                the stream segments.
            gradient: A raster indicating the gradients - sin(theta) - of the DEM
                pixels. Must have the same shape as the raster use to derive the
                stream segments.
            high_moderate: A raster indicating DEM pixels that have high-or-moderate
                burn severity. Pixels that meet this criteria should have a value
                of 1. All other pixels should be 0. Must have the same shape as
                the raster used to derive the stream segments.
            dNBR: A raster holding dNBR values for the DEM pixels. Must have the
                same shape as the raster used to derive the stream segments.
            kf_factor: A raster holding KF-factor values for the DEM pixels. Must
                have the same shape as the raster used to derive the stream segments.

        Output:
            Dict[str, numpy 1D array]: The values of the model variables for the
                input stream segments.
                'T': The mean gradient of upslope area burned at high-or-moderate severity
                'F': Mean catchment dNBR / 1000
                'S': Mean catchment KF-factor
        """

        T = burn_gradient(segments, flow_directions, gradient, high_moderate)
        F = scaled_dnbr(segments, npixels, flow_directions, dNBR)
        S = _kf_factor(segments, npixels, flow_directions, kf_factor)
        return Model._variable_dict(T, F, S)


class M3(Model):
    """
    M3  Implements the M3 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

    Terrain: Topographic ruggedness

    Fire: The proportion of upslope area burned at high-or-moderate severity

    Soil: Mean catchment soil-thickness / 100
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic model intercepts
        Ct              - Terrain coefficients
        Cf              - Fire coefficients
        Cs              - Soil coefficients

    Methods:
        parameters      - Returns model parameters for the queried rainfall durations
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments
    """

    # Model parameters
    B = [-3.71, -3.79, -3.46]
    Ct = [0.32, 0.21, 0.14]
    Cf = [0.33, 0.19, 0.10]
    Cs = [0.47, 0.36, 0.18]

    def variables(
        segments: Segments,
        npixels: SegmentValues,
        flow_directions: Raster,
        relief: Raster,
        areas: SegmentValues,
        high_moderate: Raster,
        soil_thickness: Raster,
    ) -> VariableDict:
        """
        variables  Returns the M2 terrain, fire, and soil variables for a set of stream segments
        ----------
        M3.variables(segments, npixels, flow_directions,
                                   relief, areas, high_moderate, soil_thickness)
        Returns the terrain, fire, and soil variables required to run the M3 model
        for a set of stream segments. The terrain variable is topographic ruggedness.
        The fire variable is the proportion of upslope area burned at high-or-moderate
        severity. The soil variable is mean catchment soil thickness / 100.
        Returns a dict mapping each variable to a numpy 1D array with the values
        of the variable for the stream segments.
        ----------
        Inputs:
            segments: A set of stream segments
            npixels: The number of upslope pixels for each stream segment.
            flow_directions: A raster holding TauDEM-style D8 flow directions for the
                DEM pixels. Must have the same shape as the raster used to derive
                the stream segments
            relief: A raster holding the vertical relief of the DEM pixels. Must
                have the same shape as the raster used to derive the stream segments.
            areas: The total upslope area for each stream segment. Should be in the
                same units as the data in the vertical relief raster.
            high_moderate: A raster indicating DEM pixels that have high-or-moderate
                burn severity. Pixels that meet this criteria should have a value
                of 1. All other pixels should be 0. Must have the same shape as
                the raster used to derive the stream segments.
            soil_thickness: A raster holding the soil thickness of the DEM pixels.
                Must have the same shape as the raster used to derive the stream
                segments.

        Output:
            Dict[str, numpy 1D array]: The values of the model variables for the
                input stream segments.
                'T': Topographic ruggedness
                'F': The proportion of upslope area burned at high-or-moderate severity
                'S': Mean catchment soil thickness / 100
        """

        T = ruggedness(segments, areas, relief)
        F = upslope_ratio(segments, npixels, flow_directions, high_moderate)
        S = scaled_thickness(segments, npixels, flow_directions, soil_thickness)
        return Model._variable_dict(T, F, S)


class M4(Model):
    """
    M4  Implements the M4 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

    Terrain: The proportion of upslope area burned at any severity (low-moderate-high)
        with slopes greater than 30 degrees.

    Fire: Mean catchment dNBR / 1000

    Soil: Mean catchment soil-thickness / 100
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic model intercepts
        Ct              - Terrain coefficients
        Cf              - Fire coefficients
        Cs              - Soil coefficients

    Methods:
        parameters      - Returns model parameters for the queried rainfall durations
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments
    """

    # Model parameters
    B = [-3.60, -3.64, -3.30]
    Ct = [0.51, 0.33, 0.20]
    Cf = [0.82, 0.46, 0.24]
    Cs = [0.27, 0.26, 0.13]

    def variables(
        segments: Segments,
        npixels: SegmentValues,
        flow_directions: Raster,
        burned_30: Raster,
        dNBR: Raster,
        soil_thickness: Raster,
    ) -> VariableDict:
        """
        variables  Returns the M4 terrain, fire, and soil variables for a set of stream segments
        ----------
        M4.variables(segments, npixels, flow_directions,
                                                burned_30, dNBR, soil_thickness)
        Returns the terrain, fire, and soil variables required to run the M3 model
        for a set of stream segments. The terrain variable is the proportion of
        upslope area burned at any severity (low-moderate-high) with slopes
        greater than 30. The fire variable is mean catchment dNBR / 1000. The
        soil variable is mean catchment soil thickness / 100. Returns a dict
        mapping each variable to a numpy 1D array with the values of the variable
        for the stream segments.
        ----------
        Inputs:
            segments: A set of stream segments
            npixels: The number of upslope pixels for each stream segment.
            flow_directions: A raster holding TauDEM-style D8 flow directions for the
                DEM pixels. Must have the same shape as the raster used to derive
                the stream segments
            burned_30: A raster indicating DEM pixels that are both burned at
                any level of severity (low-moderate-high) and have slopes greater
                than 30 degrees. Pixels that meet this criteria should have a value
                of 1. All other pixels should be 0. Must have the same shape as
                the raster used to derive the stream segments.
            dNBR: A raster holding dNBR values for the DEM pixels. Must have the
                same shape as the raster used to derive the stream segments.
            soil_thickness: A raster holding the soil thickness of the DEM pixels.
                Must have the same shape as the raster used to derive the stream
                segments.

        Output:
            Dict[str, numpy 1D array]: The values of the model variables for the
                input stream segments.
                'T': The proportion of upslope area burned at low-moderate-high
                    severity with slopes greater than 30
                'F': Mean catchment dNBR / 1000
                'S': Mean catchment soil / 100
        """

        T = upslope_ratio(segments, npixels, flow_directions, burned_30)
        F = scaled_dnbr(segments, npixels, flow_directions, dNBR)
        S = scaled_thickness(segments, npixels, flow_directions, soil_thickness)
        return Model._variable_dict(T, F, S)
