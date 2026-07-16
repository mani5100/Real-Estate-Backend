import logging
import sys
import functools
import inspect
from pythonjsonlogger import jsonlogger
from real_estate_backend.core.request_context import get_request_id
from real_estate_backend.core.config import settings
from rich.logging import RichHandler


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("real_estate")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger
    
    if settings.debug_mode:
        handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_level=True,
            show_path=False,
            markup=True,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        
    else:
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        
    logger.addHandler(handler)
    return logger


logger = setup_logger()


def log_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        logged_params = {
            k: str(v) for k, v in bound.arguments.items()
            if k != "db"
        }

        logger.info(
            f"[cyan]{func.__name__}[/cyan] called | "
            f"request_id=[yellow]{get_request_id()}[/yellow] | "
            f"params={logged_params}"
        )

        try:
            result = func(*args, **kwargs)
            logger.info(
                f"[green]{func.__name__}[/green] completed | "
                f"request_id=[yellow]{get_request_id()}[/yellow]"
            )
            return result

        except Exception as exc:
            logger.error(
                f"[red]{func.__name__}[/red] raised "
                f"[red]{type(exc).__name__}[/red] | "
                f"request_id=[yellow]{get_request_id()}[/yellow] | "
                f"error={str(exc)}"
            )
            raise

    return wrapper