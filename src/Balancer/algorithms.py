import asyncio
import random
from typing import List

from .section import BackendNode


class AlgorithmsMixin:
    """
    Contient les trois algorithmes de sélection de nœud.
    """

    _lock: asyncio.Lock

    async def _round_robin(
        self,
        service: str,
        nodes: List[BackendNode]
    ) -> BackendNode:

        async with self._lock:
            rr = await self._get_rr()
            idx = rr.get(service, 0) % len(nodes)
            rr[service] = idx + 1
            await self._set_rr(rr)

        return nodes[idx]

    async def _weighted(
        self,
        nodes: List[BackendNode]
    ) -> BackendNode:

        total = sum(n.weight for n in nodes)
        r = random.uniform(0, total)
        current = 0

        for node in nodes:
            current += node.weight
            if r <= current:
                return node

        return nodes[-1]

    async def _least_connections(
        self,
        nodes: List[BackendNode]
    ) -> BackendNode:

        return min(nodes, key=lambda x: x.active_connections)