"""
Middleware de logging para requisições SOAP (/soap).
Registra latência, tempo de processamento e tamanho do payload.
"""
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("soap.request")

SOAP_PREFIX = "/soap"


def _formatar_path(request: Request) -> str:
    if request.url.query:
        return f"{request.url.path}?{request.url.query}"
    return request.url.path


class SoapRequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(SOAP_PREFIX):
            return await call_next(request)

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

        logger.info(
            "requisicao concluida | %s %s | status=%s | latencia=%.2fms | "
            "processamento=%.2fms | cliente=%s | tamanho_payload=%s bytes",
            request.method,
            _formatar_path(request),
            response.status_code,
            latencia_ms,
            tempo_processamento_ms,
            cliente,
            len(body),
        )

        return response
