from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from xcore.kernel.api.rbac import get_current_user, AuthPayload
from ..dependencies import HttpDep, LBDep

logger = logging.getLogger("talion.gateway.proxy")


if TYPE_CHECKING:
    from ..section import EnvClass
    from ..Balancer import BackendNode


_HOP_BY_HOP = frozenset([
    "host", "connection", "keep-alive",
    "transfer-encoding", "te", "trailer",
    "proxy-authorization", "proxy-authenticate", "upgrade",
])


def _forward_headers(request: Request) -> dict:
    return {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }


def proxy_router(env:"EnvClass"):

    router = APIRouter(tags=["proxy"])

    @router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"], summary="Proxy vers le backend",)
    async def proxy(service: str,path: str,request: Request,lb: LBDep,client: HttpDep, user:AuthPayload= Depends(get_current_user)) -> StreamingResponse:

        body = await request.body()
        headers = _forward_headers(request)
        query = str(request.query_params)

        attempts = 0
        last_error: Exception | None = None
        tried: list[str] = []

        while attempts <= env.proxy_max_retries:

            node:Optional[BackendNode | None] = await lb.pick(service)

            if node is None:
                raise HTTPException(
                    status_code=503,
                    detail=f"Aucun backend disponible pour '{service}'",
                )

            if node.url in tried:
                break

            target = f"{node.url.rstrip('/')}/{path}"
            if query:
                target += f"?{query}"

            tried.append(node.url)
            await lb.incr_connections(service, node.url)

            try:
                resp = await client.request(
                    method=request.method,
                    url=target,
                    headers=headers,
                    content=body,
                    timeout=env.proxy_timeout,
                )

                logger.info(
                    f"[{service}] {request.method} /{path} → {node.url} ({resp.status_code})"
                )

                # Décrémente à la fin du streaming via un générateur wrappé
                async def _stream_and_decr():
                    try:
                        async for chunk in resp.aiter_bytes():
                            yield chunk
                    finally:
                        await lb.decr_connections(service, node.url)

                return StreamingResponse(
                    content=_stream_and_decr(),
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                )

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = exc
                attempts += 1

                logger.warning(
                    f"[{service}] {node.url} injoignable "
                    f"(tentative {attempts}/{env.proxy_max_retries}) : {exc}"
                )

                await lb.decr_connections(service, node.url)
                await lb.mark_unhealthy(service, node.url)

        raise HTTPException(
            status_code=502,
            detail=(
                f"Tous les backends de '{service}' ont échoué "
                f"après {attempts} tentative(s). Dernière erreur : {last_error}"
            ),
        )
    
    return router