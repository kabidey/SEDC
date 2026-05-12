"""In-memory async pub/sub used for SSE live-streaming to the frontend."""
import asyncio
import json
from typing import Any, Dict, List

_subscribers: List[asyncio.Queue] = []
_lock = asyncio.Lock()


async def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=200)
    async with _lock:
        _subscribers.append(q)
    return q


async def unsubscribe(q: asyncio.Queue):
    async with _lock:
        if q in _subscribers:
            _subscribers.remove(q)


async def publish(event: Dict[str, Any]):
    """Broadcast a JSON-serialisable event to all subscribers (non-blocking)."""
    dead = []
    async with _lock:
        snapshot = list(_subscribers)
    for q in snapshot:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(q)
    if dead:
        async with _lock:
            for q in dead:
                if q in _subscribers:
                    _subscribers.remove(q)


def subscriber_count() -> int:
    return len(_subscribers)
