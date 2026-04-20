from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl

from ..dependencies import LBDep
from xcore.kernel.api.rbac import require_role, get_current_user, AuthPayload



# ----------------------------------------------------------
# Schemas
# ----------------------------------------------------------

class AddServiceBody(BaseModel):
    name: str
    urls: List[HttpUrl]
    weight: int = 1


class SetupBody(BaseModel):
    services: Dict[str, List[HttpUrl]]
    weights: Optional[Dict[str, List[int]]] = None


# ----------------------------------------------------------
# Services
# ----------------------------------------------------------
def adminstration_router():
    router = APIRouter(prefix="/admin", tags=["Talion-admin", "Talion"], dependencies=[Depends(require_role('talion:add'))])
    @router.post("/services", status_code=201)
    async def add_service(body: AddServiceBody, lb: LBDep):
        """Ajoute un service et ses nœuds au load balancer."""
        await lb.add_service(
            name=body.name,
            urls=[str(u) for u in body.urls],
            weight=body.weight,
        )
        return {"message": f"Service '{body.name}' ajouté"}


    @router.delete("/services/{name}", dependencies=[Depends(require_role('talion:delete'))])
    async def remove_service(name: str, lb: LBDep):
        """Supprime un service et tous ses nœuds."""
        await lb.remove_service(name)
        return {"message": f"Service '{name}' supprimé"}


    @router.post("/setup", dependencies=[Depends(require_role('talion:add'))])
    async def setup(body: SetupBody, lb: LBDep):
        """Réinitialise complètement le load balancer."""
        await lb.setup(
            services={k: [str(u) for u in v] for k, v in body.services.items()},
            weights=body.weights,
        )
        return {"message": "LoadBalancer réinitialisé"}


    # ----------------------------------------------------------
    # Health
    # ----------------------------------------------------------

    @router.post("/services/{service}/nodes/unhealthy", dependencies=[Depends(require_role('talion:add'))])
    async def mark_unhealthy(service: str, url: str, lb: LBDep,):
        """Marque un nœud comme indisponible."""
        stats = await lb.get_stats()
        if service not in stats:
            raise HTTPException(404, f"Service '{service}' introuvable")
        await lb.mark_unhealthy(service, url)
        return {"message": f"Nœud '{url}' marqué unhealthy"}


    @router.post("/services/{service}/nodes/healthy",dependencies=[Depends(require_role('talion:add'))])
    async def mark_healthy(service: str, url: str, lb: LBDep):
        """Remet un nœud en service."""
        stats = await lb.get_stats()
        if service not in stats:
            raise HTTPException(404, f"Service '{service}' introuvable")
        await lb.mark_healthy(service, url)
        return {"message": f"Nœud '{url}' marqué healthy"}


    # ----------------------------------------------------------
    # Stats
    # ----------------------------------------------------------

    @router.get("/stats", dependencies=[Depends(require_role('talion:add'))])
    async def get_stats(lb: LBDep, ):
        """Retourne l'état de tous les services et nœuds."""
        return await lb.get_stats()
    
    return router