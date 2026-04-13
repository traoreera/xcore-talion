from fastapi import APIRouter

from ..dependencies import LBDep


def health_router():
    router = APIRouter(tags=["health"])


    @router.get("/health")
    async def health(lb: LBDep):
        """Santé de la gateway et résumé des backends."""
        stats = await lb.get_stats()

        summary = {
            service: {
                "total": len(nodes),
                "healthy": sum(bool(n["healthy"])
                        for n in nodes),
            }
            for service, nodes in stats.items()
        }

        degraded = [s for s, v in summary.items() if v["healthy"] == 0]

        return {
            "status": "degraded" if degraded else "ok",
            "degraded_services": degraded,
            "services": summary,
        }
    
    return router