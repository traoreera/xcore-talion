from __future__ import annotations
from typing import Any
import httpx
from .Balancer import LoadBalancer
from xcore.sdk import TrustedBase, AutoDispatchMixin, RouterRegistry, ok, error, action
from .section import EnvClass
from fastapi import FastAPI, APIRouter




class Plugin(AutoDispatchMixin, TrustedBase):


    async def on_load(self) -> None:
        
        # stage 0 : load cache servise and env configurations 
        self.cache = self.get_service('cache')
        self.env = EnvClass.from_dict(self.ctx.env)
        
        # stage 1 : load and configure balancer
        self.balancer = LoadBalancer(cache=self.cache, algorithm=self.env.algorithm)
        await self.balancer.setup(services=self.env.urls)

        # stage 2 : config http client
        self.http_client = httpx.AsyncClient()

    @action("health")
    async def ipc_health(self, payload: dict) -> dict:
        stats = await self.balancer.get_stats()
        summary = {
            service: {
                "total": len(nodes),
                "healthy": sum(bool(n["healthy"]) for n in nodes),
            }
            for service, nodes in stats.items()
        }
        degraded = [s for s, v in summary.items() if v["healthy"] == 0]
        return ok(
            data={
            "status":"degraded" if degraded else "ok",
            "degraded_services":degraded,
            "services":summary,
            }
        )

    @action("services")
    async def ipc_services(self, payload: dict) -> dict:
        return ok(
            algorithm=self.env.algorithm,
            proxy_timeout=self.env.proxy_timeout,
            proxy_max_retries=self.env.proxy_max_retries,
            services=self.env.urls,
        )


    def add_state(self) -> dict:
        return {
            "name": "Talion",
            "state": {
                "lb": self.balancer,
                "http_client": self.http_client
            }
        }
    
    def get_router(self) -> Any | None:
        from .gateway import view
        return view(env=self.env)