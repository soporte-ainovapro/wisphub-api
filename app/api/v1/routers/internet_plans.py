from fastapi import APIRouter, Depends, Path, HTTPException
from typing import List, Dict, Any

from app.services.interfaces import InternetPlanService
from app.api.deps import get_internet_plan_service
from app.schemas.internet_plans import InternetPlanListItem, InternetPlanResponse
from app.api.deps import verify_api_key

router = APIRouter(tags=["internet-plans"])


@router.get("/api/internet-plans/", response_model=List[InternetPlanListItem])
async def list_internet_plans_endpoint(
    service: InternetPlanService = Depends(get_internet_plan_service),
    _: str = Depends(verify_api_key),
):
    """
    Lista todos los planes de internet configurados en WispHub. Respuesta cacheada.
    """
    plans = await service.list_plans()

    if not plans:
        raise HTTPException(
            status_code=404, detail="No se encontraron planes de internet."
        )

    return plans


@router.get(
    "/api/internet-plans/{plan_id}",
    response_model=InternetPlanResponse | Dict[str, Any],
)
async def get_internet_plan_detail_endpoint(
    plan_id: int = Path(...),
    service: InternetPlanService = Depends(get_internet_plan_service),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene los detalles de un plan por ID (PPPOE, Simple Queue, PCQ).
    """
    return await service.get_plan_detail(plan_id)
