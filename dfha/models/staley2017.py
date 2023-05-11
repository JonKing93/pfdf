"""
staley2017  Implements the logistic models presented in Staley et al., 2017
"""

import numpy as np
from abc import ABC, abstractmethod
from dhfa import validate
from dhfa.utils import real


#####
# Variables
#####


def ruggedness(segments, area, relief):
    relief = segments.summary("max", relief)
    return relief / np.sqrt(area)


def burn_ratio(segments, npixels, flow_directions, isburned):
    return segments.catchment_mean(npixels, flow_directions, isburned)


def scaled_dnbr(segments, npixels, flow_directions, dNBR):
    dNBR = segments.catchment_mean(npixels, flow_directions, dNBR)
    return dNBR / 1000


def kf_factor(segments, npixels, flow_directions, kf_factor):
    return segments.catchment_mean(npixels, flow_directions, kf_factor)


def scaled_thickness(segments, npixels, flow_directions, soil_thickness):
    thickness = segments.catchment_mean(npixels, flow_directions, soil_thickness)
    return thickness / 100


def _kf_factor(*args, **kwargs):
    # Alias to permit both variables and functions to be named kf_factor
    return kf_factor(*args, **kwargs)


#####
# Model classes
#####


class Model(ABC):
    durations = [15, 30, 60]
    B = None
    Ct = None
    Cf = None
    Cs = None

    @classmethod
    def DurationsError(cls, durations, valid):
        bad = np.argwhere(valid == 0)[0]
        allowed = ", ".join([str(value) for value in cls.durations])
        return ValueError(
            f"Duration {bad} ({durations[bad]}) is not an allowed value. Allowed values are: {allowed}"
        )

    @classmethod
    def parameters(cls, durations=durations):
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
        for p, values in enumerate(parameters):
            parameters[p] = np.array(values)[indices]
        return parameters

    @abstractmethod
    def variables(*args, **kwargs):
        pass


class M1(Model):
    B = [-3.63, -3.61, -3.21]
    Ct = [0.41, 0.26, 0.17]
    Cf = [0.67, 0.39, 0.20]
    Cs = [0.70, 0.50, 0.220]

    def variables(
        segments, npixels, flow_directions, high_moderate_23, dNBR, kf_factor
    ):
        T = burn_ratio(npixels, flow_directions, high_moderate_23)
        F = scaled_dnbr(segments, npixels, flow_directions, dNBR)
        S = _kf_factor(segments, npixels, flow_directions, kf_factor)
        return T, F, S


class M2(Model):
    B = [-3.62, -3.61, -3.22]
    Ct = [0.64, 0.42, 0.27]
    Cf = [0.65, 0.38, 0.19]
    Cs = [0.68, 0.49, 0.22]

    def variables(
        segments, npixels, flow_directions, high_moderate, slope, dNBR, kf_factor
    ):
        T = burn_gradient(segments, npixels, flow_directions, high_moderate, slope)
        F = scaled_dnbr(segments, npixels, flow_directions, dNBR)
        S = _kf_factor(segments, npixels, flow_directions, kf_factor)
        return T, F, S


class M3(Model):
    B = [-3.71, -3.79, -3.46]
    Ct = [0.32, 0.21, 0.14]
    Cf = [0.33, 0.19, 0.10]
    Cs = [0.47, 0.36, 0.18]

    def variables(
        segments, npixels, flow_directions, relief, high_moderate_burn, soil_thickness
    ):
        T = ruggedness(segments, npixels, relief)
        F = burn_ratio(segments, npixels, flow_directions, high_moderate_burn)
        S = scaled_thickness(segments, npixels, flow_directions, soil_thickness)
        return T, F, S


class M4(Model):
    B = [-3.60, -3.64, -3.30]
    Ct = [0.51, 0.33, 0.20]
    Cf = [0.82, 0.46, 0.24]
    Cs = [0.27, 0.26, 0.13]

    def variables(segments, npixels, flow_directions, burned_30, dNBR, soil_thickness):
        T = burn_ratio(segments, npixels, flow_directions, burned_30)
        F = scaled_dnbr(segments, npixels, flow_directions, dNBR)
        S = scaled_thickness(segments, npixels, flow_directions, soil_thickness)
        return T, F, S
