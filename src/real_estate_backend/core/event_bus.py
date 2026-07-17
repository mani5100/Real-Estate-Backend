from collections import defaultdict
from typing import Callable
from real_estate_backend.core.logging import logger


class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event_name: str):
        def decorator(func: Callable):
            self._listeners[event_name].append(func)
            logger.info(f"Listener registered", extra={
                "event": event_name,
                "listener": func.__name__,
            })
            return func
        return decorator

    def emit(self, event_name: str, event) -> None:
        listeners = self._listeners.get(event_name, [])

        if not listeners:
            logger.warning(f"No listeners for event", extra={"event": event_name})
            return

        for listener in listeners:
            try:
                listener(event)
            except Exception as exc:
                logger.error(f"Listener failed", extra={
                    "event": event_name,
                    "listener": listener.__name__,
                    "error": str(exc),
                })


# Single instance — imported everywhere
event_bus = EventBus()