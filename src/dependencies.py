from typing import Annotated

import httpx
from fastapi import Depends, Request

from .Balancer import LoadBalancer

_STATE_KEY = "talion_gateway"


def get_lb(request: Request) -> LoadBalancer:
    return request.app.state.Talion_lb


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.Talion_http_client


LBDep = Annotated[LoadBalancer, Depends(get_lb)]
HttpDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]