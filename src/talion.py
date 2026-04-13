import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("talion.gateway.middleware")

# Header posé par le proxy pour permettre le suivi
_SERVICE_HEADER = "X-Talion-Service"
_NODE_HEADER = "X-Talion-Node"


class ConnectionTrackerMiddleware(BaseHTTPMiddleware):
    """
    Incrémente / décrémente le compteur de connexions actives
    d'un nœud en s'appuyant sur les headers internes posés
    par le proxy avant de transmettre la réponse.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        service = response.headers.get(_SERVICE_HEADER)
        node_url = response.headers.get(_NODE_HEADER)

        # Nettoyage des headers internes avant envoi au client
        if service and node_url:
            lb = request.app.state.lb
            await lb.decr_connections(service, node_url)

            # MutableHeaders pour supprimer les headers internes
            mutable = response.headers.mutablecopy()
            del mutable[_SERVICE_HEADER]
            del mutable[_NODE_HEADER]

        return response