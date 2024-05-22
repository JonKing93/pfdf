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


class TestVolumes:
    def test_single_run(_):
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1)
        RSE = 1

        V, Vmin, Vmax = g14._volumes(lnV, RSE, False)
        assert np.allclose(V, [100, 200, 300, 400])
        assert np.allclose(Vmin, [13.53352832, 27.06705665, 40.60058497, 54.13411329])
        assert np.allclose(
            Vmax, [738.90560989, 1477.81121979, 2216.71682968, 2955.62243957]
        )
        assert V.shape == (4,)
        assert Vmin.shape == (4,)
        assert Vmax.shape == (4,)

    def test_keepdims(_):
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1)
        RSE = 1

        V, Vmin, Vmax = g14._volumes(lnV, RSE, True)
        assert np.allclose(V.reshape(-1), [100, 200, 300, 400])
        assert np.allclose(
            Vmin.reshape(-1), [13.53352832, 27.06705665, 40.60058497, 54.13411329]
        )
        assert np.allclose(
            Vmax.reshape(-1),
            [738.90560989, 1477.81121979, 2216.71682968, 2955.62243957],
        )
        assert V.shape == (4, 1)
        assert Vmin.shape == (4, 1)
        assert Vmax.shape == (4, 1)

    def test_multiple_runs(_):
        lnV = np.log([100, 200, 300, 400]).reshape(4, 1)
        RSE = np.array([1, 1.5]).reshape(1, 2)

        V, Vmin, Vmax = g14._volumes(lnV, RSE, True)
        assert np.allclose(V.reshape(-1), [100, 200, 300, 400])
        expected = np.array(
            [
                [13.53352832, 4.97870684],
                [27.06705665, 9.95741367],
                [40.60058497, 14.93612051],
                [54.13411329, 19.91482735],
            ]
        )
        assert np.allclose(Vmin, expected)
        expected = np.array(
            [
                [738.90560989, 2008.55369232],
                [1477.81121979, 4017.10738464],
                [2216.71682968, 6025.66107696],
                [2955.62243957, 8034.21476928],
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
        V, Vmin, Vmax = g14.emergency(i15, Bmh, R)

        eV = np.array([8.92385523e01, 3.10949998e03, 1.36645970e05])
        eVmin = np.array([1.11485913e01, 3.88470492e02, 1.70712101e04])
        eVmax = [7.14307218e02, 2.48898959e04, 1.09377842e06]

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
        eVmin = np.array(
            [
                [1.11485913e01, 1.47481010e01],
                [3.88470492e02, 5.13894709e02],
                [1.70712101e04, 2.25829367e04],
            ]
        )
        eVmax = np.array(
            [
                [7.14307218e02, 9.44933289e02],
                [2.48898959e04, 3.29260165e04],
                [1.09377842e06, 1.44692314e06],
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
        eVmin = [1.11485913e01, 1.61474394e03, 2.37734224e05]
        eVmax = [7.14307218e02, 1.03459103e05, 1.52319937e07]

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3,)
            assert np.allclose(output, expected)

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
                [2.38715526e01, 5.19218976e01],
                [1.69433500e04, 3.54419081e05],
                [1.80185680e07, 5.95029203e09],
            ]
        )
        eVmax = np.array(
            [
                [1.52948672e03, 3.32671503e03],
                [1.08558623e06, 2.27081702e07],
                [1.15447708e09, 3.81244270e11],
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
        eVmin = np.array([1.11485913e01, 1.61474394e03, 2.37734224e05]).reshape(3, 1)
        eVmax = np.array([7.14307218e02, 1.03459103e05, 1.52319937e07]).reshape(3, 1)

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3, 1)
            assert np.allclose(output, expected)

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
        V, Vmin, Vmax = g14.longterm(i60, Bt, T, A, R)

        eV = np.array([345.20241331, 3622.90951263, 37508.12049657])
        eVmin = [28.33593962, 297.38652236, 3078.85401935]
        eVmax = [4205.42631537, 44136.07325785, 456942.45142678]

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
                [28.33593962, 120.12596989],
                [297.38652236, 1260.72559819],
                [3078.85401935, 13052.34024892],
            ]
        )
        eVmax = np.array(
            [
                [4205.42631537, 17828.27468111],
                [44136.07325785, 187108.26878864],
                [456942.45142678, 1937139.05002409],
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
        eVmin = [28.33593962, 1260.72559819, 22585.51397876]
        eVmax = [4205.42631537, 187108.26878864, 3351987.47954388]
        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
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
                [3.11591129e03, 6.06715907e01],
                [2.23508535e08, 2.90325870e04],
                [1.95177857e14, 6.74962974e06],
            ]
        )
        eVmax = np.array(
            [
                [4.62442237e05, 9.00446244e03],
                [3.31716077e10, 4.30881796e06],
                [2.89669624e16, 1.00173387e09],
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
        eVmin = np.array([28.33593962, 1260.72559819, 22585.51397876]).reshape(3, 1)
        eVmax = np.array([4205.42631537, 187108.26878864, 3351987.47954388]).reshape(
            3, 1
        )

        for output, expected in zip([V, Vmin, Vmax], [eV, eVmin, eVmax]):
            assert output.shape == (3, 1)
            assert np.allclose(output, expected)

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
