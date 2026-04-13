from __future__ import annotations
from .proxy import proxy_router
from .adminsitration import adminstration_router
from .health import health_router
from fastapi import APIRouter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..section import EnvClass

def view(env:EnvClass)-> "APIRouter":
    route = APIRouter(tags=["Talion"])
    route.include_router(adminstration_router())
    route.include_router(health_router())
    route.include_router(proxy_router(env=env))

    return route