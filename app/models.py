import math
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_ABS_VALUE = 1e100


class Operation(str, Enum):
    ADD = "сложение"
    SUBTRACT = "вычитание"
    MULTIPLY = "умножение"
    DIVIDE = "деление"
    POWER = "степень"
    MODULO = "остаток"


class CalculationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Operation

    a: float = Field(
        ...,
        ge=-MAX_ABS_VALUE,
        le=MAX_ABS_VALUE,
        description="Первое число",
    )

    b: float = Field(
        ...,
        ge=-MAX_ABS_VALUE,
        le=MAX_ABS_VALUE,
        description="Второе число",
    )

    @field_validator("a", "b")
    @classmethod
    def validate_finite_number(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError(
                "Значение должно быть конечным числом"
            )

        return value


class CalculationResponse(BaseModel):
    operation: Operation
    a: float
    b: float
    result: float


class HealthResponse(BaseModel):
    status: str
    version: str