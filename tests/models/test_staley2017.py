"""
test_staley2017  Unit tests for the staley2017 module
"""

import numpy as np
import pytest

from pfdf.errors import DurationsError, ShapeError
from pfdf.models import staley2017 as s17
from pfdf.segments import Segments

#####
# Fixtures
#####


# Catchment mean fixtures
@pytest.fixture
def segments5():
    stream = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 2, 2, 0],
            [0, 1, 2, 0, 0],
            [0, 1, 0, 3, 0],
            [0, 0, 0, 0, 0],
        ]
    )
    return Segments(stream)


@pytest.fixture
def flow5():
    return np.array(
        [
            [3, 3, 3, 3, 3],
            [5, 7, 1, 3, 1],
            [5, 7, 3, 7, 1],
            [5, 7, 3, 1, 1],
            [7, 7, 7, 7, 7],
        ]
    )


@pytest.fixture
def values5():
    return np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 1, 6, 7, 0],
            [0, 2, 5, 8, 0],
            [0, 3, 4, 9, 0],
            [0, 0, 0, 0, 0],
        ]
    )


@pytest.fixture
def mask5():
    return np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 1, 1, 0],
            [0, 1, 0, 1, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    ).astype(bool)


@pytest.fixture
def areas():
    return np.array([1, 4, 9]).reshape(-1)


@pytest.fixture
def npixels():
    return np.ones((3,))


def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


def check_dict(output, expected):
    assert isinstance(output, dict)
    assert len(output) == len(expected)
    assert output.keys() == expected.keys()
    for key in output.keys():
        assert np.array_equal(output[key], expected[key])


#####
# Variable Tests
#####


class TestBurnGradient:
    def test(_, segments5, flow5, values5, mask5):
        expected = np.array([2.5, 6.5, 8]).reshape(-1)
        output = s17.burn_gradient(segments5, flow5, values5, mask5)
        assert np.array_equal(output, expected)


@pytest.mark.parametrize("function", (s17.kf_factor, s17._kf_factor))
class TestKFFactor:
    def test(_, function, segments5, npixels, flow5, values5):
        expected = np.array([6, 22, 17]).reshape(-1)
        output = function(segments5, npixels, flow5, values5)
        assert np.array_equal(output, expected)


class TestRuggedness:
    def test(_, segments5, values5, areas):
        expected = np.array([3, 3.5, 3])
        output = s17.ruggedness(segments5, areas, values5)
        assert np.array_equal(output, expected)

    @pytest.mark.parametrize("bad", (0, -1))
    def test_nonpositive_area(_, segments5, values5, bad):
        areas = np.array([bad, 4, 9])
        with pytest.raises(ValueError) as error:
            s17.ruggedness(segments5, areas, values5)
        assert_contains(error, "areas")

    @pytest.mark.parametrize("N", (2, 4))
    def test_area_wrong_length(_, segments5, values5, N):
        areas = np.ones((N,))
        with pytest.raises(ShapeError) as error:
            s17.ruggedness(segments5, areas, values5)
        assert_contains(error, "areas")


class TestScaledDnbr:
    def test(_, segments5, npixels, flow5, values5):
        expected = np.array([6, 22, 17]).reshape(-1)
        expected = expected / 1000
        output = s17.scaled_dnbr(segments5, npixels, flow5, values5)
        assert np.array_equal(output, expected)


class TestScaledThickness:
    def test(_, segments5, npixels, flow5, values5):
        expected = np.array([6, 22, 17]).reshape(-1)
        expected = expected / 100
        output = s17.scaled_thickness(segments5, npixels, flow5, values5)
        assert np.array_equal(output, expected)


class TestUpslopeRatio:
    def test(_, segments5, npixels, flow5, mask5):
        expected = np.array([2, 2, 1]).reshape(-1)
        output = s17.upslope_ratio(segments5, npixels, flow5, mask5)
        assert np.array_equal(output, expected)


#####
# Model Tests
#####


@pytest.mark.parametrize(
    "model, parameters",
    (
        (
            s17.M1,
            {
                "B": [-3.63, -3.61, -3.21],
                "Ct": [0.41, 0.26, 0.17],
                "Cf": [0.67, 0.39, 0.20],
                "Cs": [0.70, 0.50, 0.220],
            },
        ),
        (
            s17.M2,
            {
                "B": [-3.62, -3.61, -3.22],
                "Ct": [0.64, 0.42, 0.27],
                "Cf": [0.65, 0.38, 0.19],
                "Cs": [0.68, 0.49, 0.22],
            },
        ),
        (
            s17.M3,
            {
                "B": [-3.71, -3.79, -3.46],
                "Ct": [0.32, 0.21, 0.14],
                "Cf": [0.33, 0.19, 0.10],
                "Cs": [0.47, 0.36, 0.18],
            },
        ),
        (
            s17.M4,
            {
                "B": [-3.60, -3.64, -3.30],
                "Ct": [0.51, 0.33, 0.20],
                "Cf": [0.82, 0.46, 0.24],
                "Cs": [0.27, 0.26, 0.13],
            },
        ),
    ),
)
class TestParameters:
    def test_all(_, model, parameters):
        output = model.parameters()
        check_dict(output, parameters)

    def test_query(_, model, parameters):
        durations = [60, 15, 60]
        expected = {key: [p[2], p[0], p[2]] for key, p in parameters.items()}
        output = model.parameters(durations)
        check_dict(output, expected)

    def test_invalid(_, model, parameters):
        durations = 45
        with pytest.raises(DurationsError):
            model.parameters(durations)


class TestVariableDict:
    def test(_):
        expected = {"T": 1, "F": True, "S": "test"}
        output = s17.Model._variable_dict(1, True, "test")
        assert output == expected


class TestM1:
    def test(_, segments5, npixels, flow5, values5, mask5):
        T = np.array([2, 2, 1]).reshape(-1)
        F = np.array([6, 22, 17]).reshape(-1) / 1000
        S = np.array([6, 22, 17]).reshape(-1)
        expected = {"T": T, "F": F, "S": S}
        output = s17.M1.variables(
            segments5,
            npixels,
            flow5,
            high_moderate_23=mask5,
            dNBR=values5,
            kf_factor=values5,
        )
        check_dict(output, expected)


class TestM2:
    def test(_, segments5, npixels, flow5, values5, mask5):
        T = np.array([2.5, 6.5, 8]).reshape(-1)
        F = np.array([6, 22, 17]).reshape(-1) / 1000
        S = np.array([6, 22, 17]).reshape(-1)
        expected = {"T": T, "F": F, "S": S}
        output = s17.M2.variables(
            segments5,
            npixels,
            flow5,
            gradient=values5,
            high_moderate=mask5,
            dNBR=values5,
            kf_factor=values5,
        )
        check_dict(output, expected)


class TestM3:
    def test(_, segments5, npixels, areas, flow5, values5, mask5):
        T = np.array([3, 3.5, 3]).reshape(-1)
        F = np.array([2, 2, 1]).reshape(-1)
        S = np.array([6, 22, 17]).reshape(-1) / 100
        expected = {"T": T, "F": F, "S": S}
        output = s17.M3.variables(
            segments5,
            npixels,
            flow5,
            relief=values5,
            areas=areas,
            high_moderate=mask5,
            soil_thickness=values5,
        )
        check_dict(output, expected)


class TestM4:
    def test(_, segments5, npixels, flow5, values5, mask5):
        T = np.array([2, 2, 1]).reshape(-1)
        F = np.array([6, 22, 17]).reshape(-1) / 1000
        S = np.array([6, 22, 17]).reshape(-1) / 100
        expected = {"T": T, "F": F, "S": S}
        output = s17.M4.variables(
            segments5,
            npixels,
            flow5,
            burned_30=mask5,
            dNBR=values5,
            soil_thickness=values5,
        )
        check_dict(output, expected)


#####
# Logistic model solver
#####


class TestSolve:
    def test(_):
        """Tests the rainfall logistic solver with some realistic values.
        Note that the expected values were calculated by solving the equation manually
        """

        p = [0.5, 0.75]  # 2 probabilities
        B, Ct, Cf, Cs = s17.M1.parameters().values()  # 3 thresholds
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        expected1 = np.array(
            [
                [6.44760213, 9.78319783, 17.63736264],
                [5.12567071, 7.79360967, 14.11609499],
                [3.40046838, 5.08450704, 9.42731278],
                [4.85943775, 7.78017241, 12.89156627],
                [3.33333333, 5.28550512, 8.53723404],
            ]
        )
        expected2 = np.array(
            [
                [8.39895611, 12.76046691, 23.67369389],
                [6.67694477, 10.16539786, 18.94728359],
                [4.42961339, 6.63184829, 12.65378058],
                [6.33013693, 10.14787131, 17.30366381],
                [4.34216004, 6.89401506, 11.45907524],
            ]
        )
        expected = np.stack((expected1, expected2), axis=2)
        output = s17.solve(p, B, Ct, T, Cf, F, Cs, S)
        assert np.allclose(output, expected, atol=1e-8)

    def test_singletons(_):
        "Test removing and retaining trailing singleton dimensions"

        p = 0.5  # 1 p-value
        B, Ct, Cf, Cs = s17.M1.parameters(15).values()  # 1 parameter run (15-minute)
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        expected = np.array(
            [6.44760213, 5.12567071, 3.40046838, 4.85943775, 3.33333333]
        ).reshape(-1)

        # Remove singletons
        output = s17.solve(p, B, Ct, T, Cf, F, Cs, S)
        assert np.allclose(output, expected, atol=1e-8)
        assert output.ndim == 1

        # Keep singletons
        output = s17.solve(p, B, Ct, T, Cf, F, Cs, S, always_3d=True)
        expected = expected.reshape(-1, 1, 1)
        assert np.allclose(output, expected, atol=1e-8)
        assert output.ndim == 3

    def test_different_nruns(_):
        p = 0.5  # 1 p-value
        B, Ct, Cf, Cs = s17.M1.parameters(15).values()  # 1 parameter run (15-minute)
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        Cf = np.append(Cf, 0.2)

        with pytest.raises(ValueError) as error:
            s17.solve(p, B, Ct, T, Cf, F, Cs, S)
        assert_contains(error, "Cf has 2")

    def test_different_nsegments(_):
        p = 0.5  # 1 p-value
        B, Ct, Cf, Cs = s17.M1.parameters(15).values()  # 1 parameter run (15-minute)
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        F += [1]

        with pytest.raises(ValueError) as error:
            s17.solve(p, B, Ct, T, Cf, F, Cs, S)
        assert_contains(error, "F has 6")

    def test_invalid_ncols(_):
        p = 0.5  # 1 p-value
        B, Ct, Cf, Cs = s17.M1.parameters().values()  # 3 parameter runs
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        F = np.array(F).reshape(-1,1)
        S = np.array(S).reshape(-1,1)

        F = np.hstack((F, F, F))
        S = np.hstack((S, S))

        with pytest.raises(ValueError) as error:
            s17.solve(p, B, Ct, T, Cf, F, Cs, S)
        assert_contains(error, "S has 2 column(s)")
