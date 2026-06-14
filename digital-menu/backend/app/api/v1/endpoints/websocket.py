"""
WebSocket endpoint — TV devices connect here to receive real-time menu updates.
Each TV subscribes to its restaurant's Redis pub/sub channel.
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.db.redis import get_redis

router = APIRouter(prefix="/ws", tags=["websocket"])

# In-memory registry: restaurant_id → set of active WebSocket connections
_connections: dict[int, set[WebSocket]] = {}


async def _broadcast(restaurant_id: int, message: dict):
    sockets = _connections.get(restaurant_id, set()).copy()
    dead = set()
    for ws in sockets:
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _connections[restaurant_id].discard(ws)


@router.websocket("/tv/{restaurant_id}/{device_id}")
async def tv_socket(websocket: WebSocket, restaurant_id: int, device_id: int):
    """
    TV app connects to: ws://host/api/v1/ws/tv/{restaurant_id}/{device_id}
    On connection: immediately receives current menu snapshot.
    On publish: receives 'menu_published' event → fetches fresh menu.
    """
    await websocket.accept()

    # Register connection
    _connections.setdefault(restaurant_id, set()).add(websocket)

    await websocket.send_json({
        "event": "connected",
        "restaurant_id": restaurant_id,
        "device_id": device_id,
        "message": "Connected to MenuVision real-time feed",
    })

    # Start Redis subscriber for this restaurant channel
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"menuvision:menu_updates")

    async def redis_listener():
        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            try:
                data = json.loads(raw["data"])
                if data.get("restaurant_id") == restaurant_id:
                    await _broadcast(restaurant_id, data)
            except Exception:
                pass

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            # Keep connection alive; TV app can send ping
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        listener_task.cancel()
        await pubsub.unsubscribe()
        _connections.get(restaurant_id, set()).discard(websocket)
