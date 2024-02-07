"""
test_gartner2014  Unit tests for the gartner2014 module
----------
Test values for the emergency and long-term models are derived from Table 2 of
Gartner et al., 2014. Expected values were calculated by solving the models by hand.
"""

import numpy as np
import pytest

from pfdf.errors import ShapeError
from pfdf.models import gartner2014 as g14

#####
# Testing Utilities
#####


def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


#####
# Internal Tests
#####


class TestValidateParameters:
    def test_valid(_):
        parameters = {"a": 1, "b": 2, "c": 3}
        parameters, nruns = g14._validate_parameters(parameters)
        assert isinstance(parameters, tuple)
        assert len(parameters) == 3
        assert parameters[0] == np.array(1).reshape(1)
        assert parameters[1] == np.array(2).reshape(1)
        assert parameters[2] == np.array(3).reshape(1)
        assert nruns == 1

    def test_valid_mixed(_):
        parameters = {"a": 1, "b": [1, 2, 3, 4], "c": [1, 2, 3, 4]}
        parameters, nruns = g14._validate_parameters(parameters)
        assert isinstance(parameters, tuple)
        assert len(parameters) == 3
        assert parameters[0] == 1
        assert np.array_equal(parameters[1], [1, 2, 3, 4])
        assert np.array_equal(parameters[2], [1, 2, 3, 4])
        assert nruns == 4

    def test_invalid_type(_):
        parameters = {"aname": "invalid"}
        with pytest.raises(TypeError) as error:
            g14._validate_parameters(parameters)
        assert_contains(error, "aname")

    def test_invalid_lengths(_):
        parameters = {"a": 1, "b": [1, 2, 3], "c": [1, 2, 3, 4]}
        with pytest.raises(ShapeError) as error:
            g14._validate_parameters(parameters)
        assert_contains(error, "b has 3 values, whereas c has 4")


class TestValidateVariables:
    def test_valid(_):
        a = np.arange(0, 10).reshape(2, 5)
        variables = {"a": a, "b": a + 1, "c": a + 2}
        output = g14._validate_variables(variables, nruns=5)
        assert isinstance(output, tuple)
        assert len(output) == 3
        assert np.array_equal(output[0], a)
        assert np.array_equal(output[1], a + 1)
        assert np.array_equal(output[2], a + 2)

    def test_mixed_ncols(_):
        a = np.arange(0, 10).reshape(2, 5)
        variables = {"a": [1, 2], "b": a + 1, "c": a + 2}
        output = g14._validate_variables(variables, nruns=5)
        assert isinstance(output, tuple)
        assert len(output) == 3
        assert np.array_equal(output[0], np.array([1, 2]).reshape(2, 1))
        assert np.array_equal(output[1], a + 1)
        assert np.array_equal(output[2], a + 2)

    def test_mixed_nrows(_):
        variables = {"a": 5, "b": [1, 2, 3, 4]}
        output = g14._validate_variables(variables, nruns=1)
        assert isinstance(output, tuple)
        assert len(output) == 2
        assert output[0] == 5
        expected = np.array([1, 2, 3, 4]).reshape(4, 1)
        assert np.array_equal(output[1], expected)

    def test_invalid_ncols_N(_):
        a = np.arange(0, 10).reshape(2, 5)
        variables = {"aname": a}
        with pytest.raises(ShapeError) as error:
            g14._validate_variables(variables, nruns=4)
        assert_contains(error, "must have either 1 or 4 runs", "aname has 5")

    def test_invalid_nrows(_):
        variables = {"aname": [1, 2, 3], "bname": [1, 2, 3, 4]}
        with pytest.raises(ShapeError) as error:
            g14._validate_variables(variables, nruns=1)
        assert_contains(error, "aname has 3 segments, whereas bname has 4")

    def test_valid_zero(_):
        a = np.arange(10).reshape(2, 5)
        variables = {"a": a}
        (output,) = g14._validate_variables(variables, nruns=5)
        assert np.array_equal(output, a)

    def test_not_positive(_):
        a = np.arange(0, 10).reshape(2, 5) + 1
        a[0, 0] = -2.2
        variables = {"aname": a}
        with pytest.raises(ValueError) as error:
            g14._validate_variables(variables, nruns=5)
        assert_contains(error, "aname")

    def test_IT_1D(_):
        variables = {
            "i15": [1, 2, 3],
            "i60": [4, 5, 6],
            "T": [7, 8, 9],
        }
        i15, i60, T = g14._validate_variables(variables, nruns=1)

        assert i15.shape == (1, 3)
        assert i60.shape == (1, 3)
        assert T.shape == (1, 3)

    def test_IT_column_vector(_):
        variables = {
            "i15": np.array([1, 2, 3]).reshape(3, 1),
            "i60": np.array([4, 5, 6]).reshape(3, 1),
            "T": np.array([7, 8, 9]).reshape(3, 1),
        }
        i15, i60, T = g14._validate_variables(variables, nruns=1)

        assert i15.shape == (3, 1)
        assert i60.shape == (3, 1)
        assert T.shape == (3, 1)


#####
# User function tests
#####


class TestEmergency:
    def test_i15_scalar(_):
        i15 = 3
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        expected = np.array([8.92385523e01, 3.10949998e03, 1.36645970e05])

        output = g14.emergency(i15, Bmh, R)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_i15_1D(_):
        i15 = [3, 6]
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]

        expected = np.array(
            [
                [8.92385523e01, 1.18050716e02],
                [3.10949998e03, 4.11345422e03],
                [1.36645970e05, 1.80764415e05],
            ]
        )
        output = g14.emergency(i15, Bmh, R)
        assert output.shape == (3, 2)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_i15_column_vector(_):
        i15 = np.array([3, 29, 72]).reshape(3, 1)
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]

        expected = np.array([8.92385523e01, 1.29251677e04, 1.90293621e06]).reshape(3)
        output = g14.emergency(i15, Bmh, R)
        assert output.shape == (3,)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_multiple_parameters(_):
        # 3 stream segments
        i15 = np.array([3, 29, 72]).reshape(3, 1)
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]

        # 2 runs
        B = [4.3, 4.4]
        Ci = [0.5, 0.6]
        Cb = [0.4, 0.5]
        Cr = [0.2, 0.3]

        expected1 = np.array([1.91079101e02, 1.35622519e05, 1.44229067e08])
        expected2 = np.array([4.15607215e02, 2.83693652e06, 4.76289276e10])
        expected = np.stack((expected1, expected2), axis=-1)

        output = g14.emergency(i15, Bmh, R, B=B, Ci=Ci, Cb=Cb, Cr=Cr)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_singletons(_):
        i15 = np.array([3, 29, 72]).reshape(3, 1)
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        expected = np.array([8.92385523e01, 1.29251677e04, 1.90293621e06]).reshape(3, 1)

        output = g14.emergency(i15, Bmh, R, keepdims=True)
        assert output.shape == (3, 1)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_invalid_nruns(_):
        # 2 runs
        B = [4.3, 4.4]
        Ci = [0.5, 0.6]
        Cb = [0.4, 0.5]
        Cr = [0.2, 0.3]

        # 3 stream segments
        i15 = np.array([3, 29, 72]).reshape(1, 3)
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]

        with pytest.raises(ShapeError) as error:
            g14.emergency(i15, Bmh, R, B=B, Ci=Ci, Cb=Cb, Cr=Cr)
        assert_contains(error, "must have either 1 or 2 runs", "i15 has 3")


class TestLongterm:
    def test_i60T_scalar(_):
        i60 = 3
        Bt = [0.1, 1.5, 16]
        T = 1
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        expected = np.array([345.20241331, 3622.90951263, 37508.12049657])

        output = g14.longterm(i60, Bt, T, A, R)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_i60T_1D(_):
        i60 = [3, 29]
        Bt = [0.1, 1.5, 16]
        T = [1, 2]
        A = [0.2, 3, 32]
        R = [93, 572, 2098]

        expected = np.array(
            [
                [345.20241331, 1463.43390267],
                [3622.90951263, 15358.78198604],
                [37508.12049657, 159010.05625553],
            ]
        )
        output = g14.longterm(i60, Bt, T, A, R)
        assert output.shape == (3, 2)
        assert np.allclose(output, expected)

    def test_i60T_column_vector(_):
        i60 = np.array([3, 29, 72]).reshape(3, 1)
        Bt = [0.1, 1.5, 16]
        T = np.array([1, 2, 3]).reshape(3, 1)
        A = [0.2, 3, 32]
        R = [93, 572, 2098]

        expected = np.array([345.20241331, 15358.78198604, 275147.88764569])
        output = g14.longterm(i60, Bt, T, A, R)
        assert output.shape == (3,)
        assert np.allclose(output, expected)

    def test_multiple_parameters(_):
        # 3 stream segments
        i60 = np.array([3, 29, 72]).reshape(3, 1)
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

        expected1 = np.array([3.79595704e04, 2.72289138e09, 2.37775307e15])
        expected2 = np.array([7.39131287e02, 3.53689316e05, 8.22273236e07])
        expected = np.stack((expected1, expected2), axis=-1)

        output = g14.longterm(i60, Bt, T, A, R, B=B, Ci=Ci, Cb=Cb, Ct=Ct, Ca=Ca, Cr=Cr)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_singletons(_):
        i60 = np.array([3, 29, 72]).reshape(3, 1)
        Bt = [0.1, 1.5, 16]
        T = np.array([1, 2, 3]).reshape(3, 1)
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        expected = np.array([345.20241331, 15358.78198604, 275147.88764569])
        expected = expected.reshape(3, 1)

        output = g14.longterm(i60, Bt, T, A, R, keepdims=True)
        assert output.shape == (3, 1)

        print(output)
        print(expected)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_invalid_nruns(_):
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
        assert_contains(error, "must have either 1 or 2 runs", "i60 has 3")
