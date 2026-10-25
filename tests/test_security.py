from unittest.mock import patch

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.security import (
    RequestBodyLimitMiddleware,
    RateLimitMiddleware,
)


ENDPOINT = "/api/v1/calculate"


def make_test_app(
    *,
    max_body_bytes=4096,
    max_requests=60,
    window_seconds=60,
    max_clients=4096,
    clock=None,
):

    test_app = FastAPI()

    test_app.add_middleware(
        RequestBodyLimitMiddleware,
        max_body_bytes=max_body_bytes,
    )

    settings = {
        "max_requests": max_requests,
        "window_seconds": window_seconds,
        "max_clients": max_clients,
    }

    if clock is not None:
        settings["clock"] = clock

    test_app.add_middleware(
        RateLimitMiddleware,
        **settings,
    )

    @test_app.post(ENDPOINT)
    async def calculate_stub(request: Request):
        return {"size": len(await request.body())}

    @test_app.get("/health")
    async def health_stub():
        return {"status": "ok"}

    return test_app



def test_request_body_exactly_4096_bytes_is_allowed():
    with TestClient(make_test_app()) as client:
        response = client.post(
            ENDPOINT,
            content=b"x" * 4096,
        )

    assert response.status_code == 200
    assert response.json()["size"] == 4096


def test_request_body_4097_bytes_is_rejected():
    with TestClient(make_test_app()) as client:
        response = client.post(
            ENDPOINT,
            content=b"x" * 4097,
        )

    assert response.status_code == 413
    assert "4096" in response.json()["detail"]


def test_streamed_request_over_limit_is_rejected():
    with TestClient(make_test_app()) as client:
        response = client.post(
            ENDPOINT,
            content=iter([
                b"a" * 3000,
                b"b" * 1097,
            ]),
        )

    assert response.status_code == 413



def test_rate_limit_allows_60_requests_and_blocks_61st():
    with TestClient(make_test_app()) as client:
        responses = [
            client.post(ENDPOINT, content=b"{}")
            for _ in range(60)
        ]

        blocked = client.post(
            ENDPOINT,
            content=b"{}",
        )

    assert all(
        response.status_code == 200
        for response in responses
    )

    assert blocked.status_code == 429

    assert (
        1 <= int(blocked.headers["Retry-After"]) <= 60
    )


def test_rate_limit_resets_after_60_seconds():
    now = [100.0]

    app = make_test_app(
        max_requests=2,
        clock=lambda: now[0],
    )

    with TestClient(app) as client:
        assert client.post(
            ENDPOINT, content=b"{}"
        ).status_code == 200

        assert client.post(
            ENDPOINT, content=b"{}"
        ).status_code == 200

        assert client.post(
            ENDPOINT, content=b"{}"
        ).status_code == 429

        now[0] += 60

        assert client.post(
            ENDPOINT, content=b"{}"
        ).status_code == 200


def test_rate_limit_is_separate_for_each_client_ip():
    app = make_test_app(max_requests=1)

    with (
        TestClient(
            app,
            client=("192.0.2.10", 50000),
        ) as first,
        TestClient(
            app,
            client=("192.0.2.11", 50000),
        ) as second,
    ):
        assert first.post(
            ENDPOINT, content=b"{}"
        ).status_code == 200

        assert first.post(
            ENDPOINT, content=b"{}"
        ).status_code == 429

        assert second.post(
            ENDPOINT, content=b"{}"
        ).status_code == 200


def test_forwarded_for_header_cannot_bypass_limit():
    with TestClient(
        make_test_app(max_requests=1)
    ) as client:

        assert client.post(
            ENDPOINT,
            content=b"{}",
        ).status_code == 200

        blocked = client.post(
            ENDPOINT,
            content=b"{}",
            headers={
                "X-Forwarded-For": "198.51.100.25"
            },
        )

    assert blocked.status_code == 429


def test_health_is_not_subject_to_rate_limit():
    with TestClient(
        make_test_app(max_requests=1)
    ) as client:

        assert client.post(
            ENDPOINT, content=b"{}"
        ).status_code == 200

        assert client.post(
            ENDPOINT, content=b"{}"
        ).status_code == 429

        assert client.get(
            "/health"
        ).status_code == 200

        assert client.get(
            "/health"
        ).status_code == 200


def test_rate_limit_client_registry_is_bounded():
    now = [100.0]

    app = make_test_app(
        max_requests=1,
        max_clients=2,
        clock=lambda: now[0],
    )

    with (
        TestClient(
            app, client=("192.0.2.10", 50000)
        ) as first,
        TestClient(
            app, client=("192.0.2.11", 50000)
        ) as second,
        TestClient(
            app, client=("192.0.2.12", 50000)
        ) as third,
    ):
        assert first.post(
            ENDPOINT, content=b"{}"
        ).status_code == 200

        assert second.post(
            ENDPOINT, content=b"{}"
        ).status_code == 200

        assert third.post(
            ENDPOINT, content=b"{}"
        ).status_code == 429

        now[0] += 60

        assert third.post(
            ENDPOINT, content=b"{}"
        ).status_code == 200



def test_middleware_enabled_in_real_api():
    from app.main import app

    classes = [
        item.cls
        for item in app.user_middleware
    ]

    assert RequestBodyLimitMiddleware in classes
    assert RateLimitMiddleware in classes

    with TestClient(app) as client:
        response = client.post(
            ENDPOINT,
            content=b"x" * 4097,
        )

    assert response.status_code == 413


def test_expression_query_is_not_executed():
    from app.main import app

    with TestClient(app) as client:
        response = client.post(
            ENDPOINT + "?expression=40%2B2",
            json={
                "operation": "сложение",
                "a": 1,
                "b": 2,
            },
        )

    assert response.status_code == 200
    assert response.json()["result"] == 3


def test_internal_error_does_not_disclose_traceback():
    from app.main import app

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as client:

        with patch(
            "app.main.calculate",
            side_effect=RuntimeError("secret error"),
        ):
            response = client.post(
                ENDPOINT,
                json={
                    "operation": "сложение",
                    "a": 1,
                    "b": 2,
                },
            )

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert "secret error" not in response.text
