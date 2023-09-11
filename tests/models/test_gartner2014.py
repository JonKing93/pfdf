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
        output = g14._validate_parameters(parameters, ncols=1)
        assert isinstance(output, tuple)
        assert len(output) == 3
        assert output[0] == np.array(1).reshape(1)
        assert output[1] == np.array(2).reshape(1)
        assert output[2] == np.array(3).reshape(1)

    def test_invalid(_):
        parameters = {"aname": "invalid"}
        with pytest.raises(TypeError) as error:
            g14._validate_parameters(parameters, ncols=1)
        assert_contains(error, "aname")

    def test_1col_Nlength(_):
        parameters = {"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]}
        output = g14._validate_parameters(parameters, ncols=1)
        assert isinstance(output, tuple)
        assert len(output) == 3
        assert np.array_equal(output[0], np.array([1, 2, 3]).reshape(3))
        assert np.array_equal(output[1], np.array([4, 5, 6]).reshape(3))
        assert np.array_equal(output[2], np.array([7, 8, 9]).reshape(3))

    def test_wrong_length(_):
        parameters = {"aname": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]}
        with pytest.raises(ShapeError) as error:
            g14._validate_parameters(parameters, ncols=2)
        assert_contains(error, "aname")


class TestValidateVariables:
    def test_valid(_):
        a = np.arange(0, 10).reshape(2, 5)
        variables = {"a": a, "b": a + 1, "c": a + 2}
        output = g14._validate_variables(variables)
        assert isinstance(output, tuple)
        assert len(output) == 3
        assert np.array_equal(output[0], a)
        assert np.array_equal(output[1], a + 1)
        assert np.array_equal(output[2], a + 2)

    def test_invalid(_):
        variables = {"aname": "invalid"}
        with pytest.raises(TypeError) as error:
            g14._validate_variables(variables)
        assert_contains(error, "aname")

    def test_different_shapes(_):
        a = np.arange(0, 10).reshape(2, 5)
        b = a.reshape(5, 2)
        variables = {"aname": a, "bname": b}
        with pytest.raises(ShapeError) as error:
            g14._validate_variables(variables)
        assert_contains(error, "bname")


#####
# User function tests
#####


class TestEmergency:
    def test(_):
        i15 = [3, 29, 72]
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        expected = np.array([8.92385523e01, 1.29251677e04, 1.90293621e06]).reshape(3)

        output = g14.emergency(i15, Bmh, R)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_multiple_runs(_):
        # 3 stream segments
        i15 = [3, 29, 72]
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
        i15 = [3, 29, 72]
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        expected = np.array([8.92385523e01, 1.29251677e04, 1.90293621e06]).reshape(3, 1)

        output = g14.emergency(i15, Bmh, R, keepdims=True)
        assert output.shape == (3, 1)
        assert np.allclose(output, expected, rtol=1e-5)


class TestLongterm:
    def test(_):
        i60 = [3, 29, 72]
        Bt = [0.1, 1.5, 16]
        T = [1, 2, 3]
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        expected = np.array([345.20241331, 15358.78198604, 275147.88764569])

        output = g14.longterm(i60, Bt, T, A, R)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_multiple_runs(_):
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

        expected1 = np.array([3.79595704e04, 2.72289138e09, 2.37775307e15])
        expected2 = np.array([7.39131287e02, 3.53689316e05, 8.22273236e07])
        expected = np.stack((expected1, expected2), axis=-1)

        output = g14.longterm(i60, Bt, T, A, R, B=B, Ci=Ci, Cb=Cb, Ct=Ct, Ca=Ca, Cr=Cr)
        assert np.allclose(output, expected, rtol=1e-5)

    def test_singletons(_):
        i60 = [3, 29, 72]
        Bt = [0.1, 1.5, 16]
        T = [1, 2, 3]
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        expected = np.array([345.20241331, 15358.78198604, 275147.88764569])
        expected = expected.reshape(3, 1)

        output = g14.longterm(i60, Bt, T, A, R, keepdims=True)
        assert output.shape == (3, 1)

        print(output)
        print(expected)
        assert np.allclose(output, expected, rtol=1e-5)
