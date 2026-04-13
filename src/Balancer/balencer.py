import asyncio
import logging
from typing import Dict, List, Literal, Optional

from .algorithms import AlgorithmsMixin
from .cache_io import CacheIOMixin
from .section import BackendNode
from xcore.services.cache.service import CacheService

logger = logging.getLogger("talion.lb")


class LoadBalancer(CacheIOMixin, AlgorithmsMixin):
    """
    Stateless LoadBalancer.
    Toute lecture / écriture passe par le cache.
    Compatible multi-instance.
    """

    def __init__(
        self,
        cache: CacheService,
        algorithm: Literal[
            "round_robin",
            "weighted",
            "least_connections",
        ] = "round_robin",
    ) -> None:
        self._cache = cache
        self._algorithm = algorithm
        self._lock = asyncio.Lock()

        self.services_key = "Talion:lb:services"
        self.rr_key = "Talion:lb:rr"

    # ----------------------------------------------------------
    # Setup
    # ----------------------------------------------------------

    async def setup(
        self,
        services: Dict[str, List[str]],
        weights: Optional[Dict[str, List[int]]] = None,
    ) -> None:

        pools = {}

        for service, urls in services.items():
            svc_weights = weights.get(service, []) if weights else []
            nodes = [
                BackendNode(
                    url=url,
                    weight=svc_weights[i] if i < len(svc_weights) else 1,
                )
                for i, url in enumerate(urls)
            ]
            pools[service] = nodes

        await self._set_pools(pools)
        await self._set_rr({})
        logger.info("LoadBalancer initialized")

    # ----------------------------------------------------------
    # Service management
    # ----------------------------------------------------------

    async def add_service(
        self,
        name: str,
        urls: List[str],
        weight: int = 1,
    ) -> None:

        pools = await self._get_pools()
        pools[name] = [BackendNode(url=u, weight=weight) for u in urls]
        await self._set_pools(pools)

        rr = await self._get_rr()
        rr[name] = 0
        await self._set_rr(rr)

    async def remove_service(self, name: str) -> None:

        pools = await self._get_pools()
        pools.pop(name, None)
        await self._set_pools(pools)

        rr = await self._get_rr()
        rr.pop(name, None)
        await self._set_rr(rr)

    # ----------------------------------------------------------
    # Health
    # ----------------------------------------------------------

    async def mark_unhealthy(self, service: str, url: str) -> None:
        pools = await self._get_pools()
        for node in pools.get(service, []):
            if node.url == url:
                node.healthy = False
                logger.warning(f"{url} unhealthy")
        await self._set_pools(pools)

    async def mark_healthy(self, service: str, url: str) -> None:
        pools = await self._get_pools()
        for node in pools.get(service, []):
            if node.url == url:
                node.healthy = True
                logger.info(f"{url} healthy")
        await self._set_pools(pools)

    # ----------------------------------------------------------
    # Pick
    # ----------------------------------------------------------

    async def pick(self, service: str) -> Optional[BackendNode]:

        pools = await self._get_pools()
        pool = pools.get(service)

        if not pool:
            logger.error(f"Unknown service: {service}")
            return None

        healthy_nodes = [n for n in pool if n.healthy]

        if not healthy_nodes:
            logger.error(f"No healthy backend for: {service}")
            return None

        match self._algorithm:
            case "round_robin":
                return await self._round_robin(service, healthy_nodes)
            case "weighted":
                return await self._weighted(healthy_nodes)
            case "least_connections":
                return await self._least_connections(healthy_nodes)
            case _:
                return healthy_nodes[0]

    # ----------------------------------------------------------
    # Connections
    # ----------------------------------------------------------

    async def incr_connections(self, service: str, url: str) -> None:
        pools = await self._get_pools()
        for node in pools.get(service, []):
            if node.url == url:
                node.active_connections += 1
        await self._set_pools(pools)

    async def decr_connections(self, service: str, url: str) -> None:
        pools = await self._get_pools()
        for node in pools.get(service, []):
            if node.url == url:
                node.active_connections = max(0, node.active_connections - 1)
        await self._set_pools(pools)

    # ----------------------------------------------------------
    # Stats
    # ----------------------------------------------------------

    async def get_stats(self) -> Dict:
        pools = await self._get_pools()
        return {
            service: [
                {
                    "url": n.url,
                    "weight": n.weight,
                    "healthy": n.healthy,
                    "connections": n.active_connections,
                }
                for n in nodes
            ]
            for service, nodes in pools.items()
        }