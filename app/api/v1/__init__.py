from fastapi import APIRouter
from app.api.v1.routers.clients import router as clients_router
from app.api.v1.routers.internet_plans import router as internet_plans_router
from app.api.v1.routers.network import router as network_router
from app.api.v1.routers.tickets import router as tickets_router

router = APIRouter()

router.include_router(clients_router)
router.include_router(internet_plans_router)
router.include_router(network_router)
router.include_router(tickets_router)

