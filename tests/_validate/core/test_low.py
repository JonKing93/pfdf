import pytest

import pfdf._validate.core._low as validate


class TestType:
    def test_success(_):
        validate.type(5, "", int, "int")
        validate.type("test", "", str, "str")

    def test_fail(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.type(5, "test", str, "str")
        assert_contains(error, "test must be a str")


class TestString:
    def test_valid(_):
        a = validate.string("some text", "")
        assert a == "some text"

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.string(5, "test name")
        assert_contains(error, "test name must be a string")


class TestOption:
    allowed = ["red", "green", "blue"]

    @pytest.mark.parametrize("input", ("red", "GREEN", "BlUe"))
    def test_valid(self, input):
        output = validate.option(input, "", self.allowed)
        assert output == input.lower()

    def test_not_string(self, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.option(5, "test name", self.allowed)
        assert_contains(error, "test name")

    def test_not_recognized(self, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.option("yellow", "test name", self.allowed)
        assert_contains(error, "test name", "yellow", "red, green, blue")


class TestCallable:
    def test_valid(_):
        def test():
            pass

        test()
        validate.callable_(test, "test")

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.callable_(5, "test name")
        assert_contains(
            error,
            'The "test name" input must be a callable object, such as a function '
            "or a static method",
        )
