"""WebSocket endpoint. Mounted by the app factory under ``/api/v1``."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket

from app.ws.hub import hub

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Hand the socket to the hub (auth handshake handled there)."""
    await hub.serve(websocket)
