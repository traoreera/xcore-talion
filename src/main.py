from __future__ import annotations
from typing import Any
import httpx
from .Balancer import LoadBalancer
from xcore.sdk import TrustedBase, AutoDispatchMixin, RouterRegistry, ok, error
from .section import EnvClass
from fastapi import FastAPI




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
        router = view(env=self.env)
        return router