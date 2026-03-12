from fastapi import APIRouter
from app.api.v1.endpoints.clients import router as clients_router
from app.api.v1.endpoints.internet_plans import router as internet_plans_router
from app.api.v1.endpoints.network import router as network_router
from app.api.v1.endpoints.tickets import router as tickets_router

router = APIRouter()

router.include_router(clients_router)
router.include_router(internet_plans_router)
router.include_router(network_router)
router.include_router(tickets_router)

@router.get("/health")
async def health_check():
    return {"status": "ok"}
