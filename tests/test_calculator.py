import pytest

from app.models import Operation
from app.services.calculator import (
    CalculatorError,
    calculate,
)


@pytest.mark.parametrize(
    ("operation", "a", "b", "expected"),
    [
        (Operation.ADD, 10, 5, 15),
        (Operation.SUBTRACT, 10, 5, 5),
        (Operation.MULTIPLY, 10, 5, 50),
        (Operation.DIVIDE, 10, 5, 2),
        (Operation.POWER, 2, 8, 256),
        (Operation.MODULO, 10, 3, 1),
    ],
)
def test_basic_operations(
    operation,
    a,
    b,
    expected,
):
    result = calculate(
        operation=operation,
        a=a,
        b=b,
    )

    assert result == pytest.approx(expected)


def test_add_negative_numbers():
    result = calculate(
        operation=Operation.ADD,
        a=-10,
        b=-5,
    )

    assert result == pytest.approx(-15)


def test_multiply_decimal_numbers():
    result = calculate(
        operation=Operation.MULTIPLY,
        a=2.5,
        b=4,
    )

    assert result == pytest.approx(10)


def test_division_by_zero():
    with pytest.raises(
        CalculatorError,
        match="Деление на ноль запрещено",
    ):
        calculate(
            operation=Operation.DIVIDE,
            a=10,
            b=0,
        )


def test_modulo_by_zero():
    with pytest.raises(
        CalculatorError,
        match="Получение остатка при делении на ноль запрещено",
    ):
        calculate(
            operation=Operation.MODULO,
            a=10,
            b=0,
        )


def test_power_limit():
    with pytest.raises(
        CalculatorError,
        match="Показатель степени",
    ):
        calculate(
            operation=Operation.POWER,
            a=2,
            b=1001,
        )