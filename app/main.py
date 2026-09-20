from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.models import (
    CalculationRequest,
    CalculationResponse,
    HealthResponse,
)
from app.services.calculator import (
    CalculatorError,
    calculate,
)


APP_VERSION = "1.0.0"


app = FastAPI(
    title="API-калькулятор",
    description=(
        "REST API для выполнения "
        "математических операций"
    ),
    version=APP_VERSION,
    redoc_url=None,
)


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next,
):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"

    return response


@app.exception_handler(CalculatorError)
async def calculator_error_handler(
    request: Request,
    exc: CalculatorError,
):
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
        },
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Система"],
    summary="Проверка состояния приложения",
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
    )


@app.post(
    "/api/v1/calculate",
    response_model=CalculationResponse,
    tags=["Калькулятор"],
    summary="Выполнить математическую операцию",
    description=(
        "Выполняет выбранную математическую "
        "операцию над двумя числами."
    ),
)
async def calculate_endpoint(
    request: CalculationRequest,
) -> CalculationResponse:

    result = calculate(
        operation=request.operation,
        a=request.a,
        b=request.b,
    )

    return CalculationResponse(
        operation=request.operation,
        a=request.a,
        b=request.b,
        result=result,
    )