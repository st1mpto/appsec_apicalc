import math

from app.models import Operation


MAX_POWER_EXPONENT = 1000


class CalculatorError(ValueError):
    """Ошибка выполнения математической операции."""


def calculate(
    operation: Operation,
    a: float,
    b: float,
) -> float:

    try:
        if operation == Operation.ADD:
            result = a + b

        elif operation == Operation.SUBTRACT:
            result = a - b

        elif operation == Operation.MULTIPLY:
            result = a * b

        elif operation == Operation.DIVIDE:
            if b == 0:
                raise CalculatorError(
                    "Деление на ноль запрещено"
                )

            result = a / b

        elif operation == Operation.MODULO:
            if b == 0:
                raise CalculatorError(
                    "Получение остатка при делении на ноль запрещено"
                )

            result = a % b

        elif operation == Operation.POWER:
            if abs(b) > MAX_POWER_EXPONENT:
                raise CalculatorError(
                    f"Показатель степени должен находиться "
                    f"в диапазоне от "
                    f"-{MAX_POWER_EXPONENT} "
                    f"до {MAX_POWER_EXPONENT}"
                )

            result = math.pow(a, b)

        else:
            raise CalculatorError(
                "Неподдерживаемая математическая операция"
            )

    except OverflowError as exc:
        raise CalculatorError(
            "Результат вычисления слишком большой"
        ) from exc

    except ValueError as exc:
        if isinstance(exc, CalculatorError):
            raise

        raise CalculatorError(
            "Невозможно выполнить операцию "
            "с указанными числами"
        ) from exc

    if not math.isfinite(result):
        raise CalculatorError(
            "Результат вычисления не является конечным числом"
        )

    return result