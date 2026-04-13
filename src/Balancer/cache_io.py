from typing import Dict, List

from .section import BackendNode
from xcore.services.cache.service import CacheService


class CacheIOMixin:
    """
    Gère la sérialisation des nœuds et les accès au cache.
    """

    _cache: CacheService
    services_key: str
    rr_key: str

    # ----------------------------------------------------------
    # Sérialisation
    # ----------------------------------------------------------

    def _serialize_node(self, node: BackendNode) -> dict:
        return {
            "url": node.url,
            "weight": node.weight,
            "healthy": node.healthy,
            "active_connections": node.active_connections,
        }

    def _deserialize_node(self, data: dict) -> BackendNode:
        node = BackendNode(
            url=data["url"],
            weight=data.get("weight", 1),
        )
        node.healthy = data.get("healthy", True)
        node.active_connections = data.get("active_connections", 0)
        return node

    # ----------------------------------------------------------
    # Pools
    # ----------------------------------------------------------

    async def _get_pools(self) -> Dict[str, List[BackendNode]]:
        raw = await self._cache.get(self.services_key) or {}
        return {
            service: [self._deserialize_node(n) for n in nodes]
            for service, nodes in raw.items()
        }

    async def _set_pools(
        self,
        pools: Dict[str, List[BackendNode]]
    ) -> None:
        raw = {
            service: [self._serialize_node(n) for n in nodes]
            for service, nodes in pools.items()
        }
        await self._cache.set(self.services_key, raw)

    # ----------------------------------------------------------
    # Round-robin index
    # ----------------------------------------------------------

    async def _get_rr(self) -> Dict[str, int]:
        return await self._cache.get(self.rr_key) or {}

    async def _set_rr(self, data: Dict[str, int]) -> None:
        await self._cache.set(self.rr_key, data)