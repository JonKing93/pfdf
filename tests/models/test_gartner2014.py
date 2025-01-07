"""
test_gartner2014  Unit tests for the gartner2014 module
----------
Test values for the emergency and long-term models are derived from Table 2 of
Gartner et al., 2014. Expected values were calculated by solving the models by hand.
"""

from math import isnan

import numpy as np
import pytest

from pfdf.errors import DimensionError, ShapeError
from pfdf.models import gartner2014 as g14

#####
# Validation
#####


class TestValidateIntensity:
    def test_not_vector(_, assert_contains):
        i15 = np.arange(8).reshape(2, 4)
        with pytest.raises(DimensionError) as error:
            g14._validate_intensity(i15, "test name")
        assert_contains(
            error, "test name can only have 1 dimension with a length greater than 1"
        )

    def test_negative(_, assert_contains):
        i15 = [2, 1, 0, -1]
        with pytest.raises(ValueError) as error:
            g14._validate_intensity(i15, "test name")
        assert_contains(
            error,
            "The data elements of test name must be greater than or equal to 0, but element [3] (value=-1) is not",
        )

    def test_valid(_):
        i15 = [1, 2, 3, 4]
        output = g14._validate_intensity(i15, "i15")
        expected = np.array(i15).reshape(1, -1, 1, 1)
        assert np.array_equal(output, expected)


class TestValidateParameters:
    def test_valid(_):
        parameters = {"a": 1, "b": 2, "c": 3}
        parameters, nruns = g14._validate_parameters(parameters)
        assert isinstance(parameters, tuple)
        assert len(parameters) == 3
        for k in range(3):
            assert parameters[k] == k + 1
            assert parameters[k].shape == (1, 1, 1, 1)
        assert nruns == 1

    def test_valid_mixed(_):
        parameters = {"a": 1, "b": [1, 2, 3, 4], "c": [1, 2, 3, 4]}
        parameters, nruns = g14._validate_parameters(parameters)
        assert isinstance(parameters, tuple)
        assert len(parameters) == 3
        assert parameters[0] == 1
        assert parameters[0].shape == (1, 1, 1, 1)

        expected = np.array([1, 2, 3, 4]).reshape(1, 1, 4, 1)
        assert np.array_equal(parameters[1], expected)
        assert np.array_equal(parameters[2], expected)
        assert nruns == 4

    def test_invalid_type(_, assert_contains):
        parameters = {"aname": "invalid"}
        with pytest.raises(TypeError) as error:
            g14._validate_parameters(parameters)
        assert_contains(error, "aname")

    def test_invalid_lengths(_, assert_contains):
        parameters = {"a": 1, "b": [1, 2, 3], "c": [1, 2, 3, 4]}
        with pytest.raises(ShapeError) as error:
            g14._validate_parameters(parameters)
        assert_contains(error, "b has 3 values, whereas c has 4")


class TestValidateVariables:
    def test_valid(_):
        a = np.arange(0, 10).reshape(2, 5)
        expected = a.reshape(2, 1, 5, 1)

        variables = {"a": a, "b": a + 1, "c": a + 2}
        output, nruns = g14._validate_variables(variables, nruns=5)
        assert isinstance(output, tuple)
        assert len(output) == 3
        assert np.array_equal(output[0], expected)
        assert np.array_equal(output[1], expected + 1)
        assert np.array_equal(output[2], expected + 2)
        assert nruns == 5

    def test_mixed_ncols(_):
        a = np.arange(0, 10).reshape(2, 5)
        expected = a.reshape(2, 1, 5, 1)
        variables = {"a": [1, 2], "b": a + 1, "c": a + 2}
        output, nruns = g14._validate_variables(variables, nruns=5)
        assert isinstance(output, tuple)
        assert len(output) == 3
        assert np.array_equal(output[0], np.array([1, 2]).reshape(2, 1, 1, 1))
        assert np.array_equal(output[1], expected + 1)
        assert np.array_equal(output[2], expected + 2)
        assert nruns == 5

    def test_mixed_nrows(_):
        variables = {"a": 5, "b": [1, 2, 3, 4]}
        output, nruns = g14._validate_variables(variables, nruns=1)
        assert isinstance(output, tuple)
        assert len(output) == 2

        assert output[0] == 5
        assert output[0].shape == (1, 1, 1, 1)

        expected = np.array([1, 2, 3, 4]).reshape(4, 1, 1, 1)
        assert np.array_equal(output[1], expected)
        assert nruns == 1

    def test_invalid_ncols_N(_, assert_contains):
        a = np.arange(0, 10).reshape(2, 5)
        variables = {"aname": a}
        with pytest.raises(ShapeError) as error:
            g14._validate_variables(variables, nruns=4)
        assert_contains(error, "must have either 1 or 4 runs", "aname has 5")

    def test_invalid_nrows(_, assert_contains):
        variables = {"aname": [1, 2, 3], "bname": [1, 2, 3, 4]}
        with pytest.raises(ShapeError) as error:
            g14._validate_variables(variables, nruns=1)
        assert_contains(error, "aname has 3 segments, whereas bname has 4")

    def test_valid_zero(_):
        a = np.arange(10).reshape(2, 5)
        variables = {"a": a}
        output, nruns = g14._validate_variables(variables, nruns=5)

        assert isinstance(output, tuple)
        assert len(output) == 1
        expected = a.reshape(2, 1, 5, 1)
        assert np.array_equal(output[0], expected)
        assert nruns == 5

    def test_not_positive(_, assert_contains):
        a = np.arange(0, 10).reshape(2, 5) + 1
        a[0, 0] = -2.2
        variables = {"aname": a}
        with pytest.raises(ValueError) as error:
            g14._validate_variables(variables, nruns=5)
        assert_contains(error, "aname")

    def test_T_1D(_):
        variables = {
            "A": [1, 2, 3],
            "B": [4, 5, 6],
            "T": [7, 8, 9],
        }
        (A, B, T), nruns = g14._validate_variables(variables, nruns=1)

        assert A.shape == (3, 1, 1, 1)
        assert B.shape == (3, 1, 1, 1)
        assert T.shape == (1, 1, 3, 1)
        assert nruns == 3

    def test_T_column_vector(_):
        variables = {
            "A": np.array([1, 2, 3]).reshape(3, 1),
            "B": np.array([4, 5, 6]).reshape(3, 1),
            "T": np.array([7, 8, 9]).reshape(3, 1),
        }
        (A, B, T), nruns = g14._validate_variables(variables, nruns=1)

        assert A.shape == (3, 1, 1, 1)
        assert B.shape == (3, 1, 1, 1)
        assert T.shape == (3, 1, 1, 1)
        assert nruns == 1


class TestValidateCI:
    def test_singleton_RSE(_):
        ci = [0.5, 0.75, 0.9]
        rse = 2
        outci, outrse = g14._validate_ci(ci, rse, nruns=5)

        expected = np.array(ci).reshape(1, 1, 1, 3)
        assert np.array_equal(outci, expected)
        expected = np.array(rse).reshape(1, 1, 1, 1)
        assert np.array_equal(outrse, expected)

    def test_multiple_RSE_cols(_):
        ci = [0.5, 0.75, 0.9]
        rse = np.array([1, 2, 3]).reshape(1, -1)
        outci, outrse = g14._validate_ci(ci, rse, nruns=5)

        expected = np.array(ci).reshape(1, 1, 1, 3)
        assert np.array_equal(outci, expected)
        expected = np.array(rse).reshape(1, 1, 1, 3)
        assert np.array_equal(outrse, expected)

    def test_RSE_set_nruns(_):
        ci = [0.5, 0.75]
        rse = [1, 2, 3, 4, 5]
        outci, outrse = g14._validate_ci(ci, rse, nruns=1)

        expected = np.array(ci).reshape(1, 1, 1, 2)
        assert np.array_equal(outci, expected)
        expected = np.array(rse).reshape(1, 1, 5, 1)
        assert np.array_equal(outrse, expected)

    def test_RSE_match_nruns(_):
        ci = 0.5
        rse = [1, 2, 3, 4]
        outci, outrse = g14._validate_ci(ci, rse, nruns=4)

        expected = np.array(ci).reshape(1, 1, 1, 1)
        assert np.array_equal(outci, expected)
        expected = np.array(rse).reshape(1, 1, 4, 1)
        assert np.array_equal(outrse, expected)

    def test_RSE_both(_):
        ci = [0.5, 0.75]
        rse = np.arange(8).reshape(4, 2)
        outci, outrse = g14._validate_ci(ci, rse, nruns=4)
        expected = np.array(ci).reshape(1, 1, 1, 2)
        assert np.array_equal(outci, expected)
        expected = np.array(rse).reshape(1, 1, 4, 2)
        assert np.array_equal(outrse, expected)

    def test_none_ci(_):
        ci, rse = g14._validate_ci(None, 1, 5)
        assert np.array_equal(ci, [])
        assert isnan(rse)

    def test_empty_ci(_):
        ci, rse = g14._validate_ci([], 1, 5)
        expected = np.array([]).reshape(1, 1, 1, -1)
        assert np.array_equal(ci, expected)
        assert isnan(rse)

    def test_ci_not_vector(_, assert_contains):
        ci = 0.1 * np.arange(8).reshape(2, 4)
        with pytest.raises(DimensionError) as error:
            g14._validate_ci(ci, 1, 1)
        assert_contains(
            error, "CI can only have 1 dimension with a length greater than 1"
        )

    def test_ci_not_in_range(_, assert_contains):
        ci = 1.2
        with pytest.raises(ValueError) as error:
            g14._validate_ci(ci, 1, 1)
        assert_contains(
            error,
            "The data elements of CI must be less than or equal to 1, but element [0] (value=1.2) is not",
        )

    def test_RSE_wrong_nCI(_, assert_contains):
        ci = [0.5, 0.75]
        rse = np.array([1, 2, 3, 4]).reshape(1, -1)
        with pytest.raises(ShapeError) as error:
            g14._validate_ci(ci, rse, 1)
        assert_contains(
            error, "RSE must have either 1 or 2 columns, but it has 4 columns instead"
        )

    def test_RSE_wrong_nruns(_, assert_contains):
        ci = [0.5, 0.75]
        rse = [1, 2]
        with pytest.raises(ShapeError) as error:
            g14._validate_ci(ci, rse, nruns=5)
        assert_contains(
            error, "RSE must have either 1 or 5 rows, but it has 2 rows instead"
        )


class TestValidate:
    def test_valid_complex(_):
        I = [1, 2, 3]
        parameters = {"A": [1, 2], "B": 5}
        variables = {
            "C": [1, 2, 3, 4, 5],
            "D": np.arange(10).reshape(5, 2),
            "T": [1, 2],
        }
        CI = [0.25, 0.5, 0.75, 0.9]
        RSE = np.arange(8).reshape(2, 4)

        I, (A, B), (C, D, T), CI, RSE = g14._validate(
            I, "", parameters, variables, CI, RSE
        )
        assert np.array_equal(I, np.array([1, 2, 3]).reshape(1, -1, 1, 1))
        assert np.array_equal(A, np.array([1, 2]).reshape(1, 1, -1, 1))
        assert np.array_equal(B, np.array([5]).reshape(1, 1, -1, 1))
        assert np.array_equal(C, np.array([1, 2, 3, 4, 5]).reshape(-1, 1, 1, 1))
        assert np.array_equal(D, np.arange(10).reshape(5, 1, 2, 1))
        assert np.array_equal(T, np.array([1, 2]).reshape(1, 1, -1, 1))
        assert np.array_equal(CI, np.array([0.25, 0.5, 0.75, 0.9]).reshape(1, 1, 1, -1))
        assert np.array_equal(RSE, np.arange(8).reshape(1, 1, 2, 4))

    def test_parameters_set_runs(_):
        I = [1, 2, 3]
        parameters = {"A": [1, 2], "B": 5}
        variables = {
            "C": [1, 2, 3, 4, 5],
            "D": np.arange(10).reshape(5, 2),
            "T": [1, 2],
        }
        CI = [0.25, 0.5, 0.75, 0.9]
        RSE = np.arange(8).reshape(2, 4)

        I, (A, B), (C, D, T), CI, RSE = g14._validate(
            I, "", parameters, variables, CI, RSE
        )
        assert np.array_equal(I, np.array([1, 2, 3]).reshape(1, -1, 1, 1))
        assert np.array_equal(A, np.array([1, 2]).reshape(1, 1, -1, 1))
        assert np.array_equal(B, np.array([5]).reshape(1, 1, -1, 1))
        assert np.array_equal(C, np.array([1, 2, 3, 4, 5]).reshape(-1, 1, 1, 1))
        assert np.array_equal(D, np.arange(10).reshape(5, 1, 2, 1))
        assert np.array_equal(T, np.array([1, 2]).reshape(1, 1, -1, 1))
        assert np.array_equal(CI, np.array([0.25, 0.5, 0.75, 0.9]).reshape(1, 1, 1, -1))
        assert np.array_equal(RSE, np.arange(8).reshape(1, 1, 2, 4))

    def test_variables_set_runs(_):
        I = [1, 2, 3]
        parameters = {"A": 1, "B": 5}
        variables = {
            "C": [1, 2, 3, 4, 5],
            "D": np.arange(10).reshape(5, 2),
            "T": [1, 2],
        }
        CI = [0.25, 0.5, 0.75, 0.9]
        RSE = np.arange(8).reshape(2, 4)

        I, (A, B), (C, D, T), CI, RSE = g14._validate(
            I, "", parameters, variables, CI, RSE
        )
        assert np.array_equal(I, np.array([1, 2, 3]).reshape(1, -1, 1, 1))
        assert np.array_equal(A, np.array([1]).reshape(1, 1, -1, 1))
        assert np.array_equal(B, np.array([5]).reshape(1, 1, -1, 1))
        assert np.array_equal(C, np.array([1, 2, 3, 4, 5]).reshape(-1, 1, 1, 1))
        assert np.array_equal(D, np.arange(10).reshape(5, 1, 2, 1))
        assert np.array_equal(T, np.array([1, 2]).reshape(1, 1, -1, 1))
        assert np.array_equal(CI, np.array([0.25, 0.5, 0.75, 0.9]).reshape(1, 1, 1, -1))
        assert np.array_equal(RSE, np.arange(8).reshape(1, 1, 2, 4))

    def test_rse_set_runs(_):
        I = [1, 2, 3]
        parameters = {"A": 1, "B": 5}
        variables = {"C": [1, 2, 3, 4, 5], "D": 1, "T": 1}
        CI = [0.25, 0.5, 0.75, 0.9]
        RSE = np.arange(8).reshape(2, 4)

        I, (A, B), (C, D, T), CI, RSE = g14._validate(
            I, "", parameters, variables, CI, RSE
        )
        assert np.array_equal(I, np.array([1, 2, 3]).reshape(1, -1, 1, 1))
        assert np.array_equal(A, np.array([1]).reshape(1, 1, -1, 1))
        assert np.array_equal(B, np.array([5]).reshape(1, 1, -1, 1))
        assert np.array_equal(C, np.array([1, 2, 3, 4, 5]).reshape(-1, 1, 1, 1))
        assert np.array_equal(D, np.array([1]).reshape(1, 1, -1, 1))
        assert np.array_equal(T, np.array([1]).reshape(1, 1, -1, 1))
        assert np.array_equal(CI, np.array([0.25, 0.5, 0.75, 0.9]).reshape(1, 1, 1, -1))
        assert np.array_equal(RSE, np.arange(8).reshape(1, 1, 2, 4))

    def test_invalid_variable_nruns(_, assert_contains):
        I = [1, 2, 3]
        parameters = {"A": [1, 2], "B": 5}
        variables = {
            "C": [1, 2, 3, 4, 5],
            "D": np.arange(20).reshape(5, 4),
            "T": [1, 2],
        }
        CI = [0.25, 0.5, 0.75, 0.9]
        RSE = np.arange(8).reshape(2, 4)

        with pytest.raises(ShapeError) as error:
            g14._validate(I, "", parameters, variables, CI, RSE)
        assert_contains(
            error, "Each variable must have either 1 or 2 runs. However, D has 4 runs."
        )

    def test_invalid_ci_nruns(_, assert_contains):
        I = [1, 2, 3]
        parameters = {"A": [1, 2], "B": 5}
        variables = {
            "C": [1, 2, 3, 4, 5],
            "D": np.arange(10).reshape(5, 2),
            "T": [1, 2],
        }
        CI = [0.25, 0.5, 0.75, 0.9]
        RSE = np.arange(12).reshape(3, 4)
        with pytest.raises(ShapeError) as error:
            g14._validate(I, "", parameters, variables, CI, RSE)
        assert_contains(
            error, "RSE must have either 1 or 2 rows, but it has 3 rows instead."
        )


#####
# Models
#####


class TestVolumes:
    def test_single_run(_):
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1, 1, 1)
        RSE = np.array([1]).reshape(1, 1, 1, 1)
        CI = np.array([0.95]).reshape(1, 1, 1, 1)

        V, Vmin, Vmax = g14._volumes(lnV, CI, RSE, False)
        assert np.allclose(V, [100, 200, 300, 400])
        assert np.allclose(Vmin, [14.08634941, 28.17269882, 42.25904823, 56.34539764])
        assert np.allclose(
            Vmax, [709.90713842, 1419.81427685, 2129.72141527, 2839.62855369]
        )
        assert V.shape == (4,)
        assert Vmin.shape == (4,)
        assert Vmax.shape == (4,)

    def test_keepdims(_):
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1, 1, 1)
        RSE = np.array([1]).reshape(1, 1, 1, 1)
        CI = np.array([0.95]).reshape(1, 1, 1, 1)

        V, Vmin, Vmax = g14._volumes(lnV, CI, RSE, True)
        assert np.allclose(V.reshape(-1), [100, 200, 300, 400])
        assert np.allclose(
            Vmin.reshape(-1), [14.08634941, 28.17269882, 42.25904823, 56.34539764]
        )
        assert np.allclose(
            Vmax.reshape(-1),
            [709.90713842, 1419.81427685, 2129.72141527, 2839.62855369],
        )
        assert V.shape == (4, 1, 1)
        assert Vmin.shape == (4, 1, 1, 1)
        assert Vmax.shape == (4, 1, 1, 1)

    def test_multiple_cis(_):
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1, 1, 1)
        RSE = np.array([1, 1.5, 1.5]).reshape(1, 1, 1, 3)
        CI = np.array([0.9, 0.9, 0.95]).reshape(1, 1, 1, 3)

        V, Vmin, Vmax = g14._volumes(lnV, CI, RSE, False)

        assert np.allclose(V.reshape(-1), [100, 200, 300, 400])
        assert V.shape == (4,)

        expected = np.array(
            [
                [19.30408167, 8.48152056, 5.28685848],
                [38.60816334, 16.96304113, 10.57371696],
                [57.91224501, 25.44456169, 15.86057544],
                [77.21632668, 33.92608226, 21.14743392],
            ]
        )
        assert np.allclose(Vmin, expected)
        assert Vmin.shape == (4, 3)

        expected = np.array(
            [
                [518.02516022, 1179.0338683, 1891.48244455],
                [1036.05032045, 2358.06773659, 3782.9648891],
                [1554.07548067, 3537.10160489, 5674.44733365],
                [2072.10064089, 4716.13547319, 7565.9297782],
            ]
        )
        assert np.allclose(Vmax, expected)
        assert Vmax.shape == (4, 3)

    def test_empty_ci(_):
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1, 1, 1)
        RSE = np.nan
        CI = np.array([]).reshape(1, 1, 1, 0)

        V, Vmin, Vmax = g14._volumes(lnV, CI, RSE, False)
        assert np.allclose(V, [100, 200, 300, 400])
        expected = np.array([]).reshape(4, 0)
        assert np.array_equal(Vmin, expected)
        assert np.array_equal(Vmax, expected)


class TestEmergency:
    def test_i15_scalar(_):
        i15 = 3
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.emergency(i15, Bmh, R)

        eV = np.array([8.92385523e01, 3.10949998e03, 1.36645970e05])
        eVmin = np.array([1.16225898e01, 4.04986879e02, 1.77970174e04])
        eVmax = [6.85175967e02, 2.38748231e04, 1.04917138e06]

        assert np.allclose(V, eV)
        assert np.allclose(Vmin, eVmin)
        assert np.allclose(Vmax, eVmax)

    def test_i15_1D(_):
        i15 = [3, 6]
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.emergency(i15, Bmh, R)

        eV = np.array(
            [
                [8.92385523e01, 1.18050716e02],
                [3.10949998e03, 4.11345422e03],
                [1.36645970e05, 1.80764415e05],
            ]
        )
        eVmin = (
            np.array(
                [
                    [1.16225898e01, 1.53751380e01],
                    [4.04986879e02, 5.35743689e02],
                    [1.77970174e04, 2.35430831e04],
                ]
            ),
        )
        eVmax = np.array(
            [
                [6.85175967e02, 9.06396525e02],
                [2.38748231e04, 3.15832104e04],
                [1.04917138e06, 1.38791396e06],
            ]
        )

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3, 2)
            assert np.allclose(output, expected)

    def test_i15_column_vector(_):
        i15 = np.array([3, 6]).reshape(-1, 1)
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.emergency(i15, Bmh, R)

        eV = np.array(
            [
                [8.92385523e01, 1.18050716e02],
                [3.10949998e03, 4.11345422e03],
                [1.36645970e05, 1.80764415e05],
            ]
        )
        eVmin = (
            np.array(
                [
                    [1.16225898e01, 1.53751380e01],
                    [4.04986879e02, 5.35743689e02],
                    [1.77970174e04, 2.35430831e04],
                ]
            ),
        )
        eVmax = np.array(
            [
                [6.85175967e02, 9.06396525e02],
                [2.38748231e04, 3.15832104e04],
                [1.04917138e06, 1.38791396e06],
            ]
        )

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3, 2)
            assert np.allclose(output, expected)

    def test_CI(_):
        i15 = 3
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.emergency(i15, Bmh, R, RSE=1, CI=0.9)

        eV = np.array([8.92385523e01, 3.10949998e03, 1.36645970e05])
        eVmin = np.array([1.72266830e01, 6.00260415e02, 2.63782497e04])
        eVmax = [4.62278154e02, 1.61079922e04, 7.07860507e05]

        assert np.allclose(V, eV)
        assert np.allclose(Vmin, eVmin)
        assert np.allclose(Vmax, eVmax)

    def test_multiple_parameters(_):
        # 3 rainfalls
        i15 = np.array([3, 29, 72]).reshape(3, 1)

        # 3 segments
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]

        # 2 runs
        B = [4.3, 4.4]
        Ci = [0.5, 0.6]
        Cb = [0.4, 0.5]
        Cr = [0.2, 0.3]

        V, Vmin, Vmax = g14.emergency(i15, Bmh, R, B=B, Ci=Ci, Cb=Cb, Cr=Cr)

        eV = np.array(
            [
                [
                    [1.91079101e02, 4.15607215e02],
                    [1.18707133e03, 3.72048390e03],
                    [5.59317713e03, 2.39010808e04],
                ],
                [
                    [2.18307260e04, 3.16908047e05],
                    [1.35622519e05, 2.83693652e06],
                    [6.39018696e05, 1.82250081e07],
                ],
                [
                    [4.92728190e06, 8.28202126e08],
                    [3.06105431e07, 7.41400188e09],
                    [1.44229067e08, 4.76289276e10],
                ],
            ]
        )
        eVmin = np.array(
            [
                [
                    [2.48864863e01, 5.41294325e01],
                    [1.54606308e02, 4.84562526e02],
                    [7.28465467e02, 3.11291983e03],
                ],
                [
                    [2.84327309e03, 4.12746750e04],
                    [1.76637212e04, 3.69487723e05],
                    [8.32269462e04, 2.37365788e06],
                ],
                [
                    [6.41738071e05, 1.07866537e08],
                    [3.98677229e06, 9.65612962e08],
                    [1.87846536e07, 6.20327734e09],
                ],
            ]
        )
        eVmax = np.array(
            [
                [
                    [1.46711039e03, 3.19104320e03],
                    [9.11436505e03, 2.85659739e04],
                    [4.29445621e04, 1.83513131e05],
                ],
                [
                    [1.67616892e05, 2.43322837e06],
                    [1.04131329e06, 2.17820737e07],
                    [4.90640246e06, 1.39932094e08],
                ],
                [
                    [3.78318008e07, 6.35895784e09],
                    [2.35028560e08, 5.69249027e10],
                    [1.10739460e09, 3.65696167e11],
                ],
            ]
        )
        assert np.allclose(V, eV)
        assert np.allclose(Vmin, eVmin)
        assert np.allclose(Vmax, eVmax)

    def test_keepdims(_):
        i15 = np.array([3, 29, 72]).reshape(3, 1)
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.emergency(i15, Bmh, R, keepdims=True)

        eV = np.array(
            [
                [[8.92385523e01], [3.70935283e02], [1.24273897e03]],
                [[3.10949998e03], [1.29251677e04], [4.33029974e04]],
                [[1.36645970e05], [5.67992312e05], [1.90293621e06]],
            ]
        )
        eVmin = np.array(
            [
                [[[1.16225898e01]], [[4.83112795e01]], [[1.61856562e02]]],
                [[[4.04986879e02]], [[1.68339713e03]], [[5.63986039e03]]],
                [[[1.77970174e04]], [[7.39763420e04]], [[2.47841840e05]]],
            ]
        )
        eVmax = np.array(
            [
                [[[6.85175967e02]], [[2.84805092e03]], [[9.54178269e03]]],
                [[[2.38748231e04]], [[9.92397796e04]], [[3.32481560e05]]],
                [[[1.04917138e06]], [[4.36106001e06]], [[1.46107946e07]]],
            ]
        )

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == expected.shape
            assert np.allclose(output, expected)

    def test_invalid_nruns(_, assert_contains):
        # 2 runs
        B = [4.3, 4.4]
        Ci = [0.5, 0.6]
        Cb = [0.4, 0.5]
        Cr = [0.2, 0.3]

        # 3 stream segments
        i15 = np.array([3, 29, 72]).reshape(1, 3)
        Bmh = [0.01, 1.11, 15.01]
        R = np.array([93, 572, 2098]).reshape(1, 3)

        with pytest.raises(ShapeError) as error:
            g14.emergency(i15, Bmh, R, B=B, Ci=Ci, Cb=Cb, Cr=Cr)
        assert_contains(error, "must have either 1 or 2 runs", "R has 3")


class TestLongterm:
    def test_T_scalar(_):
        i60 = 3
        Bt = [0.1, 1.5, 16]
        T = 1
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R)

        eV = np.array([345.20241331, 3622.90951263, 37508.12049657])
        eVmin = [29.79009541, 312.64793029, 3236.85595829]
        eVmax = [4000.14516586, 41981.64153708, 434637.53757165]

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert np.allclose(output, expected)

    def test_T_1D(_):
        i60 = [3, 29]
        Bt = [0.1, 1.5, 16]
        T = [1, 2]
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R)

        eV = np.array(
            [
                [[345.20241331, 292.29852529], [1728.30469953, 1463.43390267]],
                [[3622.90951263, 3067.68164694], [18138.608814, 15358.78198604]],
                [[37508.12049657, 31759.825206], [187789.70953128, 159010.05625553]],
            ]
        )
        eVmin = np.array(
            [
                [[29.79009541, 25.22462365], [149.14832549, 126.29064546]],
                [[312.64793029, 264.73316939], [1565.31607656, 1325.42405019]],
                [[3236.85595829, 2740.79260947], [16205.77709985, 13722.16579249]],
            ]
        )
        eVmax = np.array(
            [
                [[4000.14516586, 3387.10416796], [20027.29245919, 16958.01600913]],
                [[41981.64153708, 35547.75817681], [210187.02525005, 177974.8783499]],
                [
                    [434637.53757165, 368027.29751559],
                    [2176074.29674962, 1842580.71012533],
                ],
            ]
        )
        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == expected.shape
            assert np.allclose(output, expected)

    def test_T_column_vector(_):
        i60 = np.array([3, 29, 72]).reshape(3, 1)
        Bt = [0.1, 1.5, 16]
        T = np.array([1, 2, 3]).reshape(3, 1)
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R)

        eV = np.array(
            [
                [345.20241331, 1728.30469953, 3296.27779447],
                [3067.68164694, 15358.78198604, 29292.75840323],
                [28814.83926864, 144265.5676907, 275147.88764569],
            ]
        )
        eVmin = np.array(
            [
                [29.79009541, 149.14832549, 284.46043891],
                [264.73316939, 1325.42405019, 2527.89098246],
                [2486.64776958, 12449.75371129, 23744.56698299],
            ]
        )
        eVmax = np.array(
            [
                [4000.14516586, 20027.29245919, 38196.69033724],
                [35547.75817681, 177974.8783499, 339439.35906427],
                [333901.31575351, 1671724.1564583, 3188365.57980304],
            ]
        )
        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == expected.shape
            assert np.allclose(output, expected)

    def test_CI(_):
        i60 = 3
        Bt = [0.1, 1.5, 16]
        T = 1
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R, CI=0.9, RSE=1)

        eV = np.array([345.20241331, 3622.90951263, 37508.12049657])
        eVmin = [66.63815579, 699.36941114, 7240.59821349]
        eVmax = [1788.23535464, 18767.58280757, 194301.5012991]

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert np.allclose(output, expected)

    def test_multiple_parameters(_):
        # 3 rainfall
        i60 = [3, 29, 72]

        # 3 stream segments
        Bt = [0.1, 1.5, 16]
        T = np.array([1, 2, 3]).reshape(3, 1)
        A = [0.2, 3, 32]
        R = [93, 572, 2098]

        # 2 runs
        B = [6.5, 6.7]
        Ci = [0.8, 0.9]
        Cb = [0.3, 0.4]
        Ct = [-0.3, -0.4]
        Ca = [0.6, 0.7]
        Cr = [0.5, 0.1]

        V, Vmin, Vmax = g14.longterm(
            i60, Bt, T, A, R, B=B, Ci=Ci, Cb=Cb, Ct=Ct, Ca=Ca, Cr=Cr
        )
        assert V.shape == (3, 3, 2)
        assert Vmin.shape == (3, 3, 2)

        eV = np.array(
            [
                [
                    [3.79595704e04, 7.39131287e02],
                    [2.33100220e05, 5.69469744e03],
                    [4.82492184e05, 1.29095678e04],
                ],
                [
                    [4.43413511e08, 4.59063615e04],
                    [2.72289138e09, 3.53689316e05],
                    [5.63608994e09, 8.01794347e05],
                ],
                [
                    [1.87067248e14, 4.70788708e06],
                    [1.14873314e15, 3.62723009e07],
                    [2.37775307e15, 8.22273236e07],
                ],
            ]
        )
        eVmin = np.array(
            [
                [
                    [3.27581495e03, 6.37851611e01],
                    [2.01159596e04, 4.91437990e02],
                    [4.16378555e04, 1.11406306e03],
                ],
                [
                    [3.82654648e07, 3.96160292e03],
                    [2.34978641e08, 3.05224937e04],
                    [4.86380311e08, 6.91928248e04],
                ],
                [
                    [1.61434305e13, 4.06278751e05],
                    [9.91327658e13, 3.13020786e06],
                    [2.05194078e14, 7.09601011e06],
                ],
            ]
        )
        eVmax = np.array(
            [
                [
                    [4.39868860e05, 8.56492403e03],
                    [2.70112456e06, 6.59891575e04],
                    [5.59103501e06, 1.49593813e05],
                ],
                [
                    [5.13819818e09, 5.31954885e05],
                    [3.15523888e10, 4.09848991e06],
                    [6.53100241e10, 9.29105260e06],
                ],
                [
                    [2.16770254e15, 5.45541717e07],
                    [1.33113187e16, 4.20317077e08],
                    [2.75529865e16, 9.52835839e08],
                ],
            ]
        )
        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == expected.shape
            assert np.allclose(output, expected)

    def test_keepdims(_):
        i60 = 3
        Bt = [0.1, 1.5, 16]
        T = np.array([1, 2, 3]).reshape(3, 1)
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R, keepdims=True)

        print(repr(V))
        print(repr(Vmin))
        print(repr(Vmax))
        eV = np.array([345.20241331, 3067.68164694, 28814.83926864]).reshape(3, 1, 1)
        eVmin = np.array([29.79009541, 264.73316939, 2486.64776958]).reshape(3, 1, 1, 1)
        eVmax = np.array([4000.14516586, 35547.75817681, 333901.31575351]).reshape(
            3, 1, 1, 1
        )

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == expected.shape
            assert np.allclose(output, expected)

    def test_invalid_nruns(_, assert_contains):
        # 3 stream segments
        i60 = [3, 29, 72]
        Bt = [0.1, 1.5, 16]
        T = [1, 2, 3]
        A = [0.2, 3, 32]
        R = [93, 572, 2098]

        # 2 runs
        B = [6.5, 6.7]
        Ci = [0.8, 0.9]
        Cb = [0.3, 0.4]
        Ct = [-0.3, -0.4]
        Ca = [0.6, 0.7]
        Cr = [0.5, 0.1]

        with pytest.raises(ShapeError) as error:
            g14.longterm(i60, Bt, T, A, R, B=B, Ci=Ci, Cb=Cb, Ct=Ct, Ca=Ca, Cr=Cr)
        assert_contains(error, "must have either 1 or 2 runs", "T has 3")
