import asyncio
from fastapi import WebSocket
from real_estate_backend.core.logging import logger


class WebSocketManager:

    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, lead_id: int, websocket: WebSocket) -> None:
        """Accept connection and register it under lead_id."""
        await websocket.accept()

        if lead_id not in self._connections:
            self._connections[lead_id] = []

        self._connections[lead_id].append(websocket)

        logger.info("WebSocket connected", extra={
            "lead_id": lead_id,
            "total_connections": len(self._connections[lead_id]),
        })

    def disconnect(self, lead_id: int, websocket: WebSocket) -> None:
        """Remove websocket from registry when client disconnects."""
        if lead_id in self._connections:
            self._connections[lead_id].remove(websocket)

            if not self._connections[lead_id]:
                del self._connections[lead_id]

        logger.info("WebSocket disconnected", extra={
            "lead_id": lead_id,
        })

    async def broadcast(self, lead_id: int, message: dict) -> None:
        """
        Push message to ALL clients watching this lead.
        If a client has disconnected unexpectedly, remove it cleanly.
        """
        if lead_id not in self._connections:
            logger.info("No WebSocket clients for lead", extra={
                "lead_id": lead_id
            })
            return

        dead_connections = []

        for websocket in self._connections[lead_id]:
            try:
                await websocket.send_json(message)
                logger.info("WebSocket message sent", extra={
                    "lead_id": lead_id,
                    "message": message,
                })
            except Exception:
                dead_connections.append(websocket)

        # Clean up dead connections
        for dead in dead_connections:
            self._connections[lead_id].remove(dead)


# Single instance — shared across entire app
ws_manager = WebSocketManager()