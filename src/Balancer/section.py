import asyncio
from dataclasses import dataclass, field


@dataclass
class BackendNode:
    url:str
    weight:int = 1
    active_connections:int = 0
    healthy:bool = True
    _lock:asyncio.Lock = field(default_factory=asyncio.Lock)
