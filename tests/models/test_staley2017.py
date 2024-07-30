from math import nan

import numpy as np
import pytest

from pfdf.errors import DimensionError, DurationsError, RasterShapeError, ShapeError
from pfdf.models import staley2017 as s17
from pfdf.raster import Raster
from pfdf.utils import slope


@pytest.fixture
def slopes():
    slopes = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [10, 10, 10, 10, 10, 10, 10],
            [20, 20, 20, 20, 20, 20, 20],
            [25, 25, 25, 25, 25, 25, 25],
            [29, 29, 29, 29, 29, 29, 29],
            [31, 31, 31, 31, 31, 31, 31],
            [35, 35, 35, 35, 35, 35, 35],
        ]
    )
    return slope.from_degrees(slopes)


#####
# Solver functions
#####


class TestValidate:
    def test_valid_1_varcol(_):
        PR = np.ones(4)
        B = np.ones((6))
        Ct = np.ones((6, 1, 1))
        Cf = np.ones((1, 6, 1))
        Cs = np.ones(6)

        T = np.ones(7)
        F = np.ones((7, 1))
        S = np.ones((7, 1, 1, 1, 1))

        PR, B, Ct, Cf, Cs, T, F, S = s17._validate(PR, "", B, Ct, Cf, Cs, T, F, S)

        queries = np.ones((1, 1, 4))
        parameters = np.ones((1, 6, 1))
        variables = np.ones((7, 1, 1))

        assert np.array_equal(PR, queries)
        assert np.array_equal(B, parameters)
        assert np.array_equal(Ct, parameters)
        assert np.array_equal(Cf, parameters)
        assert np.array_equal(Cs, parameters)
        assert np.array_equal(T, variables)
        assert np.array_equal(F, variables)
        assert np.array_equal(S, variables)

    def test_valid_nruns_varcol(_):
        PR = np.ones(4)
        B = np.ones((6))
        Ct = np.ones((6, 1, 1))
        Cf = np.ones((1, 6, 1))
        Cs = np.ones(6)

        T = np.ones((7, 6))
        F = np.ones((7, 6, 1))
        S = np.ones((7, 6, 1, 1, 1))

        PR, B, Ct, Cf, Cs, T, F, S = s17._validate(PR, "", B, Ct, Cf, Cs, T, F, S)

        queries = np.ones((1, 1, 4))
        parameters = np.ones((1, 6, 1))
        variables = np.ones((7, 6, 1))

        assert np.array_equal(PR, queries)
        assert np.array_equal(B, parameters)
        assert np.array_equal(Ct, parameters)
        assert np.array_equal(Cf, parameters)
        assert np.array_equal(Cs, parameters)
        assert np.array_equal(T, variables)
        assert np.array_equal(F, variables)
        assert np.array_equal(S, variables)

    def test_invalid_vector(_, assert_contains):
        PR = np.ones((4, 4))
        B = np.ones(6)
        Ct = np.ones(6)
        Cf = np.ones(6)
        Cs = np.ones(6)

        T = np.ones(7)
        F = np.ones(7)
        S = np.ones(7)

        with pytest.raises(DimensionError) as error:
            s17._validate(PR, "PR", B, Ct, Cf, Cs, T, F, S)
        assert_contains(error, "PR")

    def test_invalid_matrix(_, assert_contains):
        PR = np.ones(4)
        B = np.ones(6)
        Ct = np.ones(6)
        Cf = np.ones(6)
        Cs = np.ones(6)

        T = np.ones((7, 6, 3))
        F = np.ones(7)
        S = np.ones(7)

        with pytest.raises(DimensionError) as error:
            s17._validate(PR, "", B, Ct, Cf, Cs, T, F, S)
        assert_contains(error, "T")

    def test_different_nruns(_, assert_contains):
        PR = np.ones(4)
        B = np.ones(6)
        Ct = np.ones(7)
        Cf = np.ones(6)
        Cs = np.ones(6)

        T = np.ones(7)
        F = np.ones(7)
        S = np.ones(7)
        with pytest.raises(ShapeError) as error:
            s17._validate(PR, "", B, Ct, Cf, Cs, T, F, S)
        assert_contains(error, "B has 6", "Ct has 7")

    def test_different_nsegments(_, assert_contains):
        PR = np.ones(4)
        B = np.ones(6)
        Ct = np.ones(6)
        Cf = np.ones(6)
        Cs = np.ones(6)

        T = np.ones(7)
        F = np.ones(6)
        S = np.ones(7)

        with pytest.raises(ShapeError) as error:
            s17._validate(PR, "", B, Ct, Cf, Cs, T, F, S)
        assert_contains(error, "T has 7", "F has 6")

    def test_bad_ncols(_, assert_contains):
        PR = np.ones(4)
        B = np.ones(6)
        Ct = np.ones(6)
        Cf = np.ones(6)
        Cs = np.ones(6)

        T = np.ones((7, 4))
        F = np.ones(7)
        S = np.ones(7)
        with pytest.raises(ShapeError) as error:
            s17._validate(PR, "", B, Ct, Cf, Cs, T, F, S)
        assert_contains(error, "T has 4 columns")

    def test_variable_sets_runs(_):
        PR = 1
        B = 1
        Ct = 1
        Cf = 1
        Cs = 1
        T = 1
        F = np.ones((1, 4))
        S = 1

        PR, B, Ct, Cf, Cs, T, F, S = s17._validate(PR, "", B, Ct, Cf, Cs, T, F, S)
        assert F.shape == (1, 4, 1)
        for array in (PR, B, Ct, Cf, Cs, T, S):
            assert array.shape == (1, 1, 1)


class TestAccumulation:
    def test_invalid_parameters(_, assert_contains):
        p = 0.5
        B = np.ones(6)
        Ct = np.ones(7)
        Cf = np.ones(6)
        Cs = np.ones(6)

        T = np.ones(7)
        F = np.ones(7)
        S = np.ones(7)
        with pytest.raises(ShapeError) as error:
            s17.accumulation(p, B, Ct, T, Cf, F, Cs, S)
        assert_contains(error, "B has 6", "Ct has 7")

    def test_invalid_p(_, assert_contains):
        p = 2
        B = np.ones(6)
        Ct = np.ones(6)
        Cf = np.ones(6)
        Cs = np.ones(6)
        T = np.ones(7)
        F = np.ones(7)
        S = np.ones(7)
        with pytest.raises(ValueError) as error:
            s17.accumulation(p, B, Ct, T, Cf, F, Cs, S)
        assert_contains(error, "p")

    def test_ncols_1(_):
        p = [0.5, 0.75]  # 2 probabilities
        B, Ct, Cf, Cs = s17.M1.parameters()  # 3 thresholds
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
        output = s17.accumulation(p, B, Ct, T, Cf, F, Cs, S)
        assert np.allclose(output, expected)

    def test_ncols_nruns(_):
        p = [0.5, 0.75]  # 2 probabilities
        B, Ct, Cf, Cs = s17.M1.parameters()  # 3 thresholds
        T = np.array([0.2, 0.22, 0.25, 0.5, 0.7, 1]).reshape(2, 3)
        F = np.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.8]).reshape(2, 3)
        S = np.array([0.4, 0.5, 0.9, 0.2, 0.3, 0.55]).reshape(2, 3)

        expected1 = np.array(
            [[6.44760213, 7.79360967, 9.42731278], [4.85943775, 5.96694215, 7.11751663]]
        )
        expected2 = np.array(
            [
                [8.39895611, 10.16539786, 12.65378058],
                [6.33013693, 7.78283023, 9.55346405],
            ]
        )
        expected = np.stack((expected1, expected2), axis=2)
        output = s17.accumulation(p, B, Ct, T, Cf, F, Cs, S)

        print(T.shape)
        print(output.shape)
        print(expected.shape)
        assert np.allclose(output, expected)

    def test_keep_trailing(_):
        p = 0.5
        B, Ct, Cf, Cs = s17.M1.parameters()  # 3 thresholds
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        expected = np.array(
            [
                [6.44760213, 9.78319783, 17.63736264],
                [5.12567071, 7.79360967, 14.11609499],
                [3.40046838, 5.08450704, 9.42731278],
                [4.85943775, 7.78017241, 12.89156627],
                [3.33333333, 5.28550512, 8.53723404],
            ]
        ).reshape(5, 3, 1)
        output = s17.accumulation(p, B, Ct, T, Cf, F, Cs, S, keepdims=True)
        assert output.shape == expected.shape
        assert np.allclose(output, expected)

    def test_remove_trailing(_):
        p = 0.5
        B, Ct, Cf, Cs = s17.M1.parameters()  # 3 thresholds
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        expected = np.array(
            [
                [6.44760213, 9.78319783, 17.63736264],
                [5.12567071, 7.79360967, 14.11609499],
                [3.40046838, 5.08450704, 9.42731278],
                [4.85943775, 7.78017241, 12.89156627],
                [3.33333333, 5.28550512, 8.53723404],
            ]
        ).reshape(5, 3)
        output = s17.accumulation(p, B, Ct, T, Cf, F, Cs, S, keepdims=False)
        assert output.shape == expected.shape
        assert np.allclose(output, expected)

    def test_invert(_):
        p = 0.5
        B, Ct, Cf, Cs = s17.M1.parameters(durations=15)
        T = 0.2
        F = 0.3
        S = 0.4

        R = s17.accumulation(p, B, Ct, T, Cf, F, Cs, S)
        output = s17.likelihood(R, B, Ct, T, Cf, F, Cs, S)
        assert np.allclose(output, p)

    def test_screen(_):
        output = s17.accumulation(p=0.5, B=10, Ct=0, T=0, Cf=0, F=0, Cs=1, S=1)
        assert np.isnan(output)

    def test_noscreen(_):
        output = s17.accumulation(
            p=0.5, B=10, Ct=0, T=0, Cf=0, F=0, Cs=1, S=1, screen=False
        )
        assert output == -10


class TestLikelihood:
    def test_invalid_parameters(_, assert_contains):
        R = 0.5
        B = np.ones(6)
        Ct = np.ones(7)
        Cf = np.ones(6)
        Cs = np.ones(6)

        T = np.ones(7)
        F = np.ones(7)
        S = np.ones(7)
        with pytest.raises(ShapeError) as error:
            s17.likelihood(R, B, Ct, T, Cf, F, Cs, S)
        assert_contains(error, "B has 6", "Ct has 7")

    def test_invalid_R(_, assert_contains):
        R = -2
        B = np.ones(6)
        Ct = np.ones(6)
        Cf = np.ones(6)
        Cs = np.ones(6)
        T = np.ones(7)
        F = np.ones(7)
        S = np.ones(7)
        with pytest.raises(ValueError) as error:
            s17.likelihood(R, B, Ct, T, Cf, F, Cs, S)
        assert_contains(error, "R")

    def test_ncols_1(_):
        R = [4, 5]
        B, Ct, Cf, Cs = s17.M1.parameters()  # 3 thresholds
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        expected1 = np.array(
            [
                [0.2013304, 0.10583586, 0.07712972],
                [0.31062478, 0.14714137, 0.09108984],
                [0.65475346, 0.31647911, 0.13610789],
                [0.34479458, 0.14754339, 0.09850031],
                [0.67392689, 0.2935924, 0.15368325],
            ]
        )
        expected2 = np.array(
            [
                [0.30682605, 0.14616523, 0.09112296],
                [0.47776468, 0.21517654, 0.11174891],
                [0.84651174, 0.4850045, 0.18130959],
                [0.52622591, 0.21585281, 0.12292695],
                [0.85996508, 0.45140389, 0.20915937],
            ]
        )
        expected = np.stack((expected1, expected2), axis=2)

        output = s17.likelihood(R, B, Ct, T, Cf, F, Cs, S)
        assert np.allclose(output, expected)

    def test_ncols_nruns(_):
        R = [4, 5]
        B, Ct, Cf, Cs = s17.M1.parameters()  # 3 thresholds
        T = np.array([0.2, 0.22, 0.25, 0.5, 0.7, 1]).reshape(2, 3)
        F = np.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.8]).reshape(2, 3)
        S = np.array([0.4, 0.5, 0.9, 0.2, 0.3, 0.55]).reshape(2, 3)

        expected1 = np.array(
            [[0.2013304, 0.14714137, 0.13610789], [0.34479458, 0.23325894, 0.19686573]]
        )
        expected2 = np.array(
            [[0.30682605, 0.21517654, 0.18130959], [0.52622591, 0.35778291, 0.27788039]]
        )
        expected = np.stack((expected1, expected2), axis=2)

        output = s17.likelihood(R, B, Ct, T, Cf, F, Cs, S)
        assert np.allclose(output, expected)

    def test_keep_trailing(_):
        R = 4
        B, Ct, Cf, Cs = s17.M1.parameters()  # 3 thresholds
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        expected = np.array(
            [
                [0.2013304, 0.10583586, 0.07712972],
                [0.31062478, 0.14714137, 0.09108984],
                [0.65475346, 0.31647911, 0.13610789],
                [0.34479458, 0.14754339, 0.09850031],
                [0.67392689, 0.2935924, 0.15368325],
            ]
        ).reshape(5, 3, 1)

        output = s17.likelihood(R, B, Ct, T, Cf, F, Cs, S, keepdims=True)
        assert output.shape == expected.shape
        assert np.allclose(output, expected)

    def test_remove_trailing(_):
        R = 4
        B, Ct, Cf, Cs = s17.M1.parameters()  # 3 thresholds
        T = [0.2, 0.22, 0.25, 0.5, 1]  # 5 stream segments
        F = [0.3, 0.4, 0.5, 0.6, 0.7]
        S = [0.4, 0.5, 0.9, 0.2, 0.3]

        expected = np.array(
            [
                [0.2013304, 0.10583586, 0.07712972],
                [0.31062478, 0.14714137, 0.09108984],
                [0.65475346, 0.31647911, 0.13610789],
                [0.34479458, 0.14754339, 0.09850031],
                [0.67392689, 0.2935924, 0.15368325],
            ]
        ).reshape(5, 3)

        output = s17.likelihood(R, B, Ct, T, Cf, F, Cs, S, keepdims=False)
        assert output.shape == expected.shape
        assert np.allclose(output, expected)

    def test_invert(_):
        R = 4
        B, Ct, Cf, Cs = s17.M1.parameters(durations=15)
        T = 0.2
        F = 0.3
        S = 0.4

        p = s17.likelihood(R, B, Ct, T, Cf, F, Cs, S)
        output = s17.accumulation(p, B, Ct, T, Cf, F, Cs, S)
        assert np.allclose(output, R)


#####
# Shared Model Methods
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
        B, Ct, Cf, Cs = model.parameters()
        assert np.array_equal(B, parameters["B"])
        assert np.array_equal(Ct, parameters["Ct"])
        assert np.array_equal(Cf, parameters["Cf"])
        assert np.array_equal(Cs, parameters["Cs"])

    def test_query(_, model, parameters):
        durations = [60, 15, 60]
        B, Ct, Cf, Cs = model.parameters(durations)
        parameters = {
            key: np.array(values)[[2, 0, 2]] for key, values in parameters.items()
        }
        assert np.array_equal(B, parameters["B"])
        assert np.array_equal(Ct, parameters["Ct"])
        assert np.array_equal(Cf, parameters["Cf"])
        assert np.array_equal(Cs, parameters["Cs"])

    def test_invalid(_, model, parameters):
        durations = 45
        with pytest.raises(DurationsError):
            model.parameters(durations)


class TestModelValidate:
    def test_invalid_segments(_, assert_contains):
        with pytest.raises(TypeError) as error:
            s17.Model._validate(5, [], [])
        assert_contains(error, "segments", "pfdf.segments.Segments")

    def test_invalid_raster(_, segments, flow, assert_contains):
        a = np.arange(10).reshape(2, 5)
        with pytest.raises(RasterShapeError) as error:
            s17.Model._validate(segments, [flow, a], ["flow", "test raster"])
        assert_contains(error, "test raster")

    def test_valid(_, segments, flow, mask):
        rasters = [flow, mask]
        raster1, raster2 = s17.Model._validate(segments, rasters, ["", ""])

        expected1 = Raster.from_array(
            flow.values, nodata=0, transform=flow.transform, crs=26911
        )
        expected2 = Raster.from_array(mask, transform=flow.transform, crs=26911)
        assert raster1 == expected1
        assert raster2 == expected2


class TestValidateOmitnan:
    def test_bool(_):
        output = s17.Model._validate_omitnan(True, rasters=["a", "b", "c"])
        assert output == {"a": True, "b": True, "c": True}

    def test_dict(_):
        input = {"a": True, "b": False}
        output = s17.Model._validate_omitnan(input, rasters=["a", "b", "c"])
        assert output == {"a": True, "b": False, "c": False}

    def test_other(_, assert_contains):
        with pytest.raises(TypeError) as error:
            s17.Model._validate_omitnan("invalid", rasters=["a"])
        assert_contains(error, "omitnan must either be a boolean or a dict")

    def test_extra_key(_, assert_contains):
        input = {"a": True, "b": False}
        with pytest.raises(ValueError) as error:
            s17.Model._validate_omitnan(input, rasters=["a"])
        assert_contains(error, "unrecognized key")

    def test_invalid_value(_, assert_contains):
        input = {"a": "invalid"}
        with pytest.raises(TypeError) as error:
            s17.Model._validate_omitnan(input, rasters=["a"])
        assert_contains(error, "omitnan['a'] is not a bool.")


class TestTerrainMask:
    def test_not_boolean(_, mask2, slopes, assert_contains):
        mask = mask2.astype(int)
        mask[0, 0] = 2
        mask = Raster(mask, "mask")
        with pytest.raises(ValueError) as error:
            s17.Model._terrain_mask(mask, slopes, 23)
        assert_contains(error, "mask")

    def test_valid(_, mask, slopes):
        slopes = Raster(slopes)
        mask = Raster(mask)
        output = s17.Model._terrain_mask(mask, slopes, threshold_degrees=23)
        expected = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 0, 1, 1, 0],
                [0, 0, 1, 1, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert np.array_equal(output, expected)

    def test_nodata(_, mask, slopes):
        slopes[5, 3] = -999
        slopes = Raster.from_array(slopes, nodata=-999)
        mask = Raster(mask)
        output = s17.Model._terrain_mask(mask, slopes, 23)
        expected = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 0, 1, 1, 0],
                [0, 0, 1, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert np.array_equal(output, expected)


#####
# Model variables
#####


class TestM1:
    def test_terrain(_, segments, slopes, mask):
        output = s17.M1.terrain(segments, mask, slopes)
        T = [3 / 5, 0, 0, 1, 1 / 2, 7 / 11]
        assert np.array_equal(output, T)

    def test_fire(_, segments, flow):
        output = s17.M1.fire(segments, flow)
        F = [23 / 5000, 7 / 1000, 3 / 1000, 5 / 1000, 25 / 4000, 62 / 11000]
        assert np.array_equal(output, F)
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = s17.M1.fire(segments, flow, True)
        F = [0.001, nan, 0.003, 0.005, 0.0055, 13 / 4000]
        assert np.array_equal(output, F, equal_nan=True)

    def test_soil(_, segments, flow):
        output = s17.M1.soil(segments, flow)
        S = [23 / 5, 7, 3, 5, 25 / 4, 62 / 11]
        assert np.array_equal(output, S)
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = s17.M1.soil(segments, flow, True)
        S = [1, nan, 3, 5, 5.5, 13 / 4]
        assert np.array_equal(output, S, equal_nan=True)

    def test_invalid(_, flow, assert_contains):
        with pytest.raises(TypeError) as error:
            s17.M1.variables(5, flow, flow, flow, flow)
        assert_contains(error, "segments")

    def test(_, segments, flow, slopes, mask):
        output = s17.M1.variables(segments, mask, slopes, flow, flow)
        T = [3 / 5, 0, 0, 1, 1 / 2, 7 / 11]
        F = [23 / 5000, 7 / 1000, 3 / 1000, 5 / 1000, 25 / 4000, 62 / 11000]
        S = [23 / 5, 7, 3, 5, 25 / 4, 62 / 11]
        assert np.array_equal(output[0], T)
        assert np.array_equal(output[1], F)
        assert np.array_equal(output[2], S)

    def test_omitnan(_, segments, flow, slopes, mask):
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = s17.M1.variables(segments, mask, slopes, flow, flow, omitnan=True)
        T = [3 / 5, 0, 0, 1, 1 / 2, 7 / 11]
        F = [0.001, nan, 0.003, 0.005, 0.0055, 13 / 4000]
        S = [1, nan, 3, 5, 5.5, 13 / 4]
        assert np.array_equal(output[0], T)
        assert np.array_equal(output[1], F, equal_nan=True)
        assert np.array_equal(output[2], S, equal_nan=True)

    def test_mixed_nan(_, segments, flow, slopes, mask):
        values = flow.values.copy().astype(float)
        values[values == 0] = nan
        flow = Raster.from_array(values, nodata=7)
        output = s17.M1.variables(segments, mask, slopes, flow, flow, omitnan=True)
        T = [3 / 5, 0, 0, 1, 1 / 2, 7 / 11]
        F = [0.001, nan, 0.003, 0.005, 0.0055, 13 / 4000]
        S = [1, nan, 3, 5, 5.5, 13 / 4]
        assert np.array_equal(output[0], T)
        assert np.array_equal(output[1], F, equal_nan=True)
        assert np.array_equal(output[2], S, equal_nan=True)


class TestM2:
    def test_invalid(_, flow, assert_contains):
        with pytest.raises(TypeError) as error:
            s17.M2.variables(5, flow, flow, flow, flow)
        assert_contains(error, "segments")

    def test_terrain(_, segments, mask, slopes, flow):
        output = s17.M2.terrain(segments, slopes, mask)
        T = [0.36914289, 0.25783416, 0.25783416, 0.42261826, 0.34022621, 0.38240609]
        assert np.allclose(output, T, equal_nan=True)

        values = flow.values.copy()
        nodatas = values == 7
        slopes[nodatas] = nan
        slopes = Raster.from_array(slopes, nodata=nan)

        output = s17.M2.terrain(segments, slopes, mask, True)
        T = [0.45371394, nan, 0.25783416, 0.42261826, 0.42261826, 0.4381661]
        assert np.allclose(output, T, equal_nan=True)

    def test_fire(_, segments, flow):
        output = s17.M2.fire(segments, flow)
        F = [23 / 5000, 7 / 1000, 3 / 1000, 5 / 1000, 25 / 4000, 62 / 11000]
        assert np.array_equal(output, F)
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = s17.M2.fire(segments, flow, True)
        F = [0.001, nan, 0.003, 0.005, 0.0055, 13 / 4000]
        assert np.array_equal(output, F, equal_nan=True)

    def test_soil(_, segments, flow):
        output = s17.M2.soil(segments, flow)
        S = [23 / 5, 7, 3, 5, 25 / 4, 62 / 11]
        assert np.array_equal(output, S)
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = s17.M2.soil(segments, flow, True)
        S = [1, nan, 3, 5, 5.5, 13 / 4]
        assert np.array_equal(output, S, equal_nan=True)

    def test(_, segments, flow, slopes, mask):
        output = s17.M2.variables(segments, mask, slopes, flow, flow)
        T = [0.36914289, 0.25783416, 0.25783416, 0.42261826, 0.34022621, 0.38240609]
        F = [23 / 5000, 7 / 1000, 3 / 1000, 5 / 1000, 25 / 4000, 62 / 11000]
        S = [23 / 5, 7, 3, 5, 25 / 4, 62 / 11]
        assert np.allclose(output[0], T)
        assert np.array_equal(output[1], F)
        assert np.array_equal(output[2], S)

    def test_omitnan(_, segments, flow, slopes, mask):
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)

        nodatas = values == 7
        slopes[nodatas] = nan
        slopes = Raster.from_array(slopes, nodata=nan)

        output = s17.M2.variables(segments, mask, slopes, flow, flow, omitnan=True)
        T = [0.45371394, nan, 0.25783416, 0.42261826, 0.42261826, 0.4381661]
        F = [0.001, nan, 0.003, 0.005, 0.0055, 13 / 4000]
        S = [1, nan, 3, 5, 5.5, 13 / 4]
        assert np.allclose(output[0], T, equal_nan=True)
        assert np.array_equal(output[1], F, equal_nan=True)
        assert np.array_equal(output[2], S, equal_nan=True)

    def test_mixed_nan(_, segments, flow, slopes, mask):
        values = flow.values.copy().astype(float)
        values[values == 0] = nan
        flow = Raster.from_array(values, nodata=7)

        nodatas = values == 7
        slopes[nodatas] = nan
        slopes = Raster.from_array(slopes, nodata=nan)

        output = s17.M2.variables(segments, mask, slopes, flow, flow, omitnan=True)
        T = [0.45371394, nan, 0.25783416, 0.42261826, 0.42261826, 0.4381661]
        F = [0.001, nan, 0.003, 0.005, 0.0055, 13 / 4000]
        S = [1, nan, 3, 5, 5.5, 13 / 4]
        assert np.allclose(output[0], T, equal_nan=True)
        assert np.array_equal(output[1], F, equal_nan=True)
        assert np.array_equal(output[2], S, equal_nan=True)


class TestM3:
    def test_invalid(_, flow, assert_contains):
        with pytest.raises(TypeError) as error:
            s17.M3.variables(5, flow, flow, flow)
        assert_contains(error, "segments")

    def test_terrain(_, segments, flow):
        output = s17.M3.terrain(segments, flow)
        T = np.array([1, 7, 3, 5, 6, 7]) / np.sqrt(segments.area() * 1e6)
        assert np.array_equal(output, T)

    def test_fire(_, segments, mask2):
        output = s17.M3.fire(segments, mask2)
        F = [0, 1, 1, 1, 1, 4 / 11]
        assert np.array_equal(output, F)

    def test_soil(_, segments, flow):
        output = s17.M3.soil(segments, flow)
        S = [23 / 500, 7 / 100, 3 / 100, 5 / 100, 25 / 400, 62 / 1100]
        assert np.array_equal(output, S)
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = s17.M3.soil(segments, flow, True)
        S = [0.01, nan, 0.03, 0.05, 0.055, 13 / 400]
        assert np.array_equal(output, S, equal_nan=True)

    def test(_, segments, mask2, flow):
        output = s17.M3.variables(segments, mask2, flow, flow)
        T = np.array([1, 7, 3, 5, 6, 7]) / np.sqrt(segments.area() * 1e6)
        F = [0, 1, 1, 1, 1, 4 / 11]
        S = [23 / 500, 7 / 100, 3 / 100, 5 / 100, 25 / 400, 62 / 1100]
        assert np.array_equal(output[0], T)
        assert np.array_equal(output[1], F)
        assert np.array_equal(output[2], S)

    def test_omitnan(_, segments, mask2, flow):
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = s17.M3.variables(segments, mask2, flow, flow, omitnan=True)
        T = np.array([1, nan, 3, 5, 6, nan]) / np.sqrt(segments.area() * 1e6)
        F = [0, 1, 1, 1, 1, 4 / 11]
        S = [0.01, nan, 0.03, 0.05, 0.055, 13 / 400]
        assert np.array_equal(output[0], T, equal_nan=True)
        assert np.array_equal(output[1], F)
        assert np.array_equal(output[2], S, equal_nan=True)

    def test_mixed_nan(_, segments, mask2, flow):
        values = flow.values.copy().astype(float)
        values[values == 0] = nan
        flow = Raster.from_array(values, nodata=7)
        output = s17.M3.variables(segments, mask2, flow, flow, omitnan=True)
        T = np.array([1, nan, 3, 5, 6, nan]) / np.sqrt(segments.area() * 1e6)
        F = [0, 1, 1, 1, 1, 4 / 11]
        S = [0.01, nan, 0.03, 0.05, 0.055, 13 / 400]
        assert np.array_equal(output[0], T, equal_nan=True)
        assert np.array_equal(output[1], F)
        assert np.array_equal(output[2], S, equal_nan=True)


class TestM4:
    def test_invalid(_, flow, assert_contains):
        with pytest.raises(TypeError) as error:
            s17.M4.variables(5, flow, flow, flow, flow)
        assert_contains(error, "segments")

    def test_terrain(_, segments, mask, slopes):
        slopes[3:, :] = 31
        output = s17.M4.terrain(segments, mask, slopes)
        T = [3 / 5, 0, 0, 1, 1 / 2, 7 / 11]
        assert np.array_equal(output, T)

    def test_fire(_, segments, flow):
        output = s17.M4.fire(segments, flow)
        F = [23 / 5000, 7 / 1000, 3 / 1000, 5 / 1000, 25 / 4000, 62 / 11000]
        assert np.array_equal(output, F)
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = s17.M4.fire(segments, flow, True)
        F = [0.001, nan, 0.003, 0.005, 0.0055, 13 / 4000]
        assert np.array_equal(output, F, equal_nan=True)

    def test_soil(_, segments, flow):
        output = s17.M4.soil(segments, flow)
        S = [23 / 500, 7 / 100, 3 / 100, 5 / 100, 25 / 400, 62 / 1100]
        assert np.array_equal(output, S)
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = s17.M4.soil(segments, flow, True)
        S = [0.01, nan, 0.03, 0.05, 0.055, 13 / 400]
        assert np.array_equal(output, S, equal_nan=True)

    def test(_, segments, mask, flow, slopes):
        slopes[3:, :] = 31
        output = s17.M4.variables(segments, mask, slopes, flow, flow)
        T = [3 / 5, 0, 0, 1, 1 / 2, 7 / 11]
        F = [23 / 5000, 7 / 1000, 3 / 1000, 5 / 1000, 25 / 4000, 62 / 11000]
        S = [23 / 500, 7 / 100, 3 / 100, 5 / 100, 25 / 400, 62 / 1100]
        assert np.array_equal(output[0], T)
        assert np.array_equal(output[1], F)
        assert np.array_equal(output[2], S)

    def test_omitnan(_, segments, mask, flow, slopes):
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        slopes[3:, :] = 31
        output = s17.M4.variables(segments, mask, slopes, flow, flow, omitnan=True)
        T = [3 / 5, 0, 0, 1, 1 / 2, 7 / 11]
        F = [0.001, nan, 0.003, 0.005, 0.0055, 13 / 4000]
        S = [0.01, nan, 0.03, 0.05, 0.055, 13 / 400]
        assert np.array_equal(output[0], T)
        assert np.array_equal(output[1], F, equal_nan=True)
        assert np.array_equal(output[2], S, equal_nan=True)

    def test_mixed_nan(_, segments, mask, flow, slopes):
        values = flow.values.copy().astype(float)
        values[values == 0] = nan
        flow = Raster.from_array(values, nodata=7)
        slopes[3:, :] = 31
        output = s17.M4.variables(segments, mask, slopes, flow, flow, omitnan=True)
        T = [3 / 5, 0, 0, 1, 1 / 2, 7 / 11]
        F = [0.001, nan, 0.003, 0.005, 0.0055, 13 / 4000]
        S = [0.01, nan, 0.03, 0.05, 0.055, 13 / 400]
        assert np.array_equal(output[0], T)
        assert np.array_equal(output[1], F, equal_nan=True)
        assert np.array_equal(output[2], S, equal_nan=True)
