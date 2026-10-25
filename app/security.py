from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from collections import deque
from math import ceil
from threading import Lock
from time import monotonic

class RequestBodyLimitMiddleware:

    def __init__(
        self,
        app: ASGIApp,
        max_body_bytes: int = 4096,
    ):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ):
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or scope.get("path") != "/api/v1/calculate"
        ):
            await self.app(scope, receive, send)
            return

        async def reject():
            response = JSONResponse(
                status_code=413,
                content={
                    "detail": "Размер запроса превышает 4096 байт"
                },
            )
            await response(scope, receive, send)

        for name, value in scope.get("headers", []):
            if name.lower() == b"content-length":
                try:
                    if int(value) > self.max_body_bytes:
                        await reject()
                        return
                except ValueError:
                    pass

        body = bytearray()

        while True:
            message = await receive()

            if message["type"] == "http.disconnect":
                return

            if message["type"] != "http.request":
                continue

            chunk = message.get("body", b"")

            if len(body) + len(chunk) > self.max_body_bytes:
                await reject()
                return

            body.extend(chunk)

            if not message.get("more_body", False):
                break

        delivered = False

        async def replay_body():
            nonlocal delivered

            if not delivered:
                delivered = True
                return {
                    "type": "http.request",
                    "body": bytes(body),
                    "more_body": False,
                }

            return await receive()

        await self.app(scope, replay_body, send)


class RateLimitMiddleware:
    """Ограничение частоты обращений к API по IP-адресу."""

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = 60,
        window_seconds: int = 60,
        max_clients: int = 4096,
        clock=monotonic,
    ):
        if min(max_requests, window_seconds, max_clients) <= 0:
            raise ValueError("Лимиты должны быть положительными")

        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self.clock = clock

        self._requests: dict[str, deque[float]] = {}
        self._lock = Lock()

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ):
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or scope.get("path") != "/api/v1/calculate"
        ):
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        now = self.clock()
        retry_after = None

        with self._lock:
            history = self._requests.get(client_ip)

            if history is None:
                if len(self._requests) >= self.max_clients:
                    expired = [
                        ip
                        for ip, requests in self._requests.items()
                        if not requests
                        or now - requests[-1] >= self.window_seconds
                    ]

                    for ip in expired:
                        del self._requests[ip]

                if len(self._requests) >= self.max_clients:
                    retry_after = self.window_seconds
                else:
                    history = deque()
                    self._requests[client_ip] = history

            if history is not None:
                while (
                    history
                    and now - history[0] >= self.window_seconds
                ):
                    history.popleft()

                if len(history) >= self.max_requests:
                    retry_after = max(
                        1,
                        ceil(
                            self.window_seconds
                            - (now - history[0])
                        ),
                    )
                else:
                    history.append(now)

        if retry_after is not None:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Превышен лимит запросов. "
                        "Повторите позже."
                    )
                },
                headers={
                    "Retry-After": str(retry_after)
                },
            )

            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
