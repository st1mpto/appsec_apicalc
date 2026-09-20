import pytest


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.parametrize(
    ("operation", "a", "b", "expected"),
    [
        ("сложение", 10, 5, 15),
        ("вычитание", 10, 5, 5),
        ("умножение", 10, 5, 50),
        ("деление", 10, 5, 2),
        ("степень", 2, 8, 256),
        ("остаток", 10, 3, 1),
    ],
)
def test_calculate_operations(
    client,
    operation,
    a,
    b,
    expected,
):
    response = client.post(
        "/api/v1/calculate",
        json={
            "operation": operation,
            "a": a,
            "b": b,
        },
    )

    assert response.status_code == 200
    assert response.json()["result"] == pytest.approx(expected)


def test_division_by_zero(client):
    response = client.post(
        "/api/v1/calculate",
        json={
            "operation": "деление",
            "a": 10,
            "b": 0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Деление на ноль запрещено"


def test_invalid_operation(client):
    response = client.post(
        "/api/v1/calculate",
        json={
            "operation": "корень",
            "a": 10,
            "b": 2,
        },
    )

    assert response.status_code == 422


def test_invalid_number(client):
    response = client.post(
        "/api/v1/calculate",
        json={
            "operation": "сложение",
            "a": "abc",
            "b": 5,
        },
    )

    assert response.status_code == 422