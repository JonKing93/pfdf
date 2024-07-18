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
# Internal Tests
#####


class TestVolumes:
    def test_single_run(_):
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1)
        RSE = 1
        CI = 0.95

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
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1)
        RSE = 1
        CI = 0.95

        V, Vmin, Vmax = g14._volumes(lnV, CI, RSE, True)
        assert np.allclose(V.reshape(-1), [100, 200, 300, 400])
        assert np.allclose(
            Vmin.reshape(-1), [14.08634941, 28.17269882, 42.25904823, 56.34539764]
        )
        assert np.allclose(
            Vmax.reshape(-1),
            [709.90713842, 1419.81427685, 2129.72141527, 2839.62855369],
        )
        assert V.shape == (4, 1)
        assert Vmin.shape == (4, 1)
        assert Vmax.shape == (4, 1)

    def test_multiple_runs(_):
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1)
        RSE = np.array([1, 1.5, 1.5]).reshape(1, 3)
        CI = np.array([0.9, 0.9, 0.95]).reshape(1, 3)

        V, Vmin, Vmax = g14._volumes(lnV, CI, RSE, True)
        assert np.allclose(V.reshape(-1), [100, 200, 300, 400])
        expected = np.array(
            [
                [19.30408167, 8.48152056, 5.28685848],
                [38.60816334, 16.96304113, 10.57371696],
                [57.91224501, 25.44456169, 15.86057544],
                [77.21632668, 33.92608226, 21.14743392],
            ]
        )
        assert np.allclose(Vmin, expected)
        expected = np.array(
            [
                [518.02516022, 1179.0338683, 1891.48244455],
                [1036.05032045, 2358.06773659, 3782.9648891],
                [1554.07548067, 3537.10160489, 5674.44733365],
                [2072.10064089, 4716.13547319, 7565.9297782],
            ]
        )
        assert np.allclose(Vmax, expected)


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
        (output,) = g14._validate_variables(variables, nruns=5)
        assert np.array_equal(output, a)

    def test_not_positive(_, assert_contains):
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
        i15 = np.array([3, 29, 72]).reshape(3, 1)
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.emergency(i15, Bmh, R)

        eV = np.array([8.92385523e01, 1.29251677e04, 1.90293621e06]).reshape(3)
        eVmin = [1.16225898e01, 1.68339713e03, 2.47841840e05]
        eVmax = [6.85175967e02, 9.92397796e04, 1.46107946e07]

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3,)
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
        # 3 stream segments
        i15 = np.array([3, 29, 72]).reshape(3, 1)
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
                [1.91079101e02, 4.15607215e02],
                [1.35622519e05, 2.83693652e06],
                [1.44229067e08, 4.76289276e10],
            ]
        )
        eVmin = np.array(
            [
                [2.48864863e01, 5.41294325e01],
                [1.76637212e04, 3.69487723e05],
                [1.87846536e07, 6.20327734e09],
            ]
        )
        eVmax = np.array(
            [
                [1.46711039e03, 3.19104320e03],
                [1.04131329e06, 2.17820737e07],
                [1.10739460e09, 3.65696167e11],
            ]
        )
        assert np.allclose(V, eV)
        assert np.allclose(Vmin, eVmin)
        assert np.allclose(Vmax, eVmax)

    def test_singletons(_):
        i15 = np.array([3, 29, 72]).reshape(3, 1)
        Bmh = [0.01, 1.11, 15.01]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.emergency(i15, Bmh, R, keepdims=True)

        eV = np.array([8.92385523e01, 1.29251677e04, 1.90293621e06]).reshape(3, 1)
        eVmin = np.array([1.16225898e01, 1.68339713e03, 2.47841840e05]).reshape(3, 1)
        eVmax = np.array([6.85175967e02, 9.92397796e04, 1.46107946e07]).reshape(3, 1)

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3, 1)
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
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R)

        eV = np.array([345.20241331, 3622.90951263, 37508.12049657])
        eVmin = [29.79009541, 312.64793029, 3236.85595829]
        eVmax = [4000.14516586, 41981.64153708, 434637.53757165]

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert np.allclose(output, expected)

    def test_i60T_1D(_):
        i60 = [3, 29]
        Bt = [0.1, 1.5, 16]
        T = [1, 2]
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R)

        eV = np.array(
            [
                [345.20241331, 1463.43390267],
                [3622.90951263, 15358.78198604],
                [37508.12049657, 159010.05625553],
            ]
        )
        eVmin = np.array(
            [
                [29.79009541, 126.29064546],
                [312.64793029, 1325.42405019],
                [3236.85595829, 13722.16579249],
            ]
        )
        eVmax = np.array(
            [
                [4000.14516586, 16958.01600913],
                [41981.64153708, 177974.8783499],
                [434637.53757165, 1842580.71012533],
            ]
        )
        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3, 2)
            assert np.allclose(output, expected)

    def test_i60T_column_vector(_):
        i60 = np.array([3, 29, 72]).reshape(3, 1)
        Bt = [0.1, 1.5, 16]
        T = np.array([1, 2, 3]).reshape(3, 1)
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R)

        eV = np.array([345.20241331, 15358.78198604, 275147.88764569])
        eVmin = [29.79009541, 1325.42405019, 23744.56698299]
        eVmax = [4000.14516586, 177974.8783499, 3188365.57980304]
        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3,)
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

        V, Vmin, Vmax = g14.longterm(
            i60, Bt, T, A, R, B=B, Ci=Ci, Cb=Cb, Ct=Ct, Ca=Ca, Cr=Cr
        )
        eV = np.array(
            [
                [3.79595704e04, 7.39131287e02],
                [2.72289138e09, 3.53689316e05],
                [2.37775307e15, 8.22273236e07],
            ]
        )
        eVmin = np.array(
            [
                [3.27581495e03, 6.37851611e01],
                [2.34978641e08, 3.05224937e04],
                [2.05194078e14, 7.09601011e06],
            ]
        )
        eVmax = np.array(
            [
                [4.39868860e05, 8.56492403e03],
                [3.15523888e10, 4.09848991e06],
                [2.75529865e16, 9.52835839e08],
            ]
        )
        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert np.allclose(output, expected)

    def test_singletons(_):
        i60 = np.array([3, 29, 72]).reshape(3, 1)
        Bt = [0.1, 1.5, 16]
        T = np.array([1, 2, 3]).reshape(3, 1)
        A = [0.2, 3, 32]
        R = [93, 572, 2098]
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R, keepdims=True)

        eV = np.array([345.20241331, 15358.78198604, 275147.88764569]).reshape(3, 1)
        eVmin = np.array([29.79009541, 1325.42405019, 23744.56698299]).reshape(3, 1)
        eVmax = np.array([4000.14516586, 177974.8783499, 3188365.57980304]).reshape(
            3, 1
        )

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3, 1)
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
        assert_contains(error, "must have either 1 or 2 runs", "i60 has 3")
