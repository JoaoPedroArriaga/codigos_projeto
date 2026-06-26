"""
Middleware de logging de requisições HTTP.
Registra latência, tempo de processamento e tamanho do payload ao final de cada requisição.
"""
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("api.request")

SKIP_PAYLOAD_PREFIXES = ("/static/", "/favicon.ico")


def _tamanho_payload(body: bytes, path: str) -> str:
    if any(path.startswith(prefix) for prefix in SKIP_PAYLOAD_PREFIXES):
        return "-"
    return f"{len(body)} bytes"


def _formatar_path(request: Request) -> str:
    if request.url.query:
        return f"{request.url.path}?{request.url.query}"
    return request.url.path


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        inicio = time.perf_counter()

        body = b""
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            body = await request.body()
            if body:

                async def receive():
                    return {"type": "http.request", "body": body, "more_body": False}

                request = Request(request.scope, receive)

        inicio_processamento = time.perf_counter()
        response = await call_next(request)
        tempo_processamento_ms = (time.perf_counter() - inicio_processamento) * 1000
        latencia_ms = (time.perf_counter() - inicio) * 1000

        cliente = request.client.host if request.client else "-"
        tamanho_payload = _tamanho_payload(body, request.url.path)

        logger.info(
            "requisicao concluida | %s %s | status=%s | latencia=%.2fms | "
            "processamento=%.2fms | cliente=%s | tamanho_payload=%s",
            request.method,
            _formatar_path(request),
            response.status_code,
            latencia_ms,
            tempo_processamento_ms,
            cliente,
            tamanho_payload,
        )

        return response
