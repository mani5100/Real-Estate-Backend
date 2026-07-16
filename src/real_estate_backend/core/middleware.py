import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from real_estate_backend.core.logging import logger
from real_estate_backend.core.request_context import set_request_id, get_request_id

METHOD_COLORS = {
    "GET": "green",
    "POST": "blue",
    "PATCH": "yellow",
    "DELETE": "red",
}
def status_color(status: int) -> str:
    if status < 300:
        return "green"
    if status < 400:
        return "yellow"
    return "red"



class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_id(request_id)

        method = request.method
        color = METHOD_COLORS.get(method, "white")

        logger.info(
            f"[{color}]{method}[/{color}] "
            f"[white]{request.url.path}[/white] | "
            f"request_id=[yellow]{request_id}[/yellow] | "
            f"[cyan]started[/cyan]"
        )

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        sc = response.status_code
        sc_color = status_color(sc)

        logger.info(
            f"[{color}]{method}[/{color}] "
            f"[white]{request.url.path}[/white] | "
            f"status=[{sc_color}]{sc}[/{sc_color}] | "
            f"duration=[magenta]{duration_ms}ms[/magenta] | "
            f"request_id=[yellow]{request_id}[/yellow]"
        )

        response.headers["X-Request-ID"] = request_id
        return response