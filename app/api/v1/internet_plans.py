from fastapi import APIRouter, Depends, Path, HTTPException

from app.domain.models.responses.response_actions import ResponseAction, PlanAction
from app.domain.models.responses.response_types import ResponseType
from app.domain.models.internet_plans import InternetPlanListItem, InternetPlanResponse
from typing import List, Dict, Any
from app.services.internet_plans_service import get_plan_type, get_queue_plan, list_internet_plans, get_pppoe_plan
from app.api.dependencies import verify_api_key

router = APIRouter(tags=["internet-plans"])

@router.get("/api/internet-plans/", response_model=List[InternetPlanListItem])
async def list_internet_plans_endpoint(_: str = Depends(verify_api_key)):
    """
    Lista todos los planes de internet configurados en el sistema WispHub.
    Esta consulta está cacheada internamente para mejorar el rendimiento y evitar
    llamadas redundantes continuas a la API externa.
    """
    plans = await list_internet_plans()

    if not plans:
        raise HTTPException(
            status_code=404,
            detail=PlanAction.NOT_FOUND.value if hasattr(PlanAction.NOT_FOUND, 'value') else "Not found"
        )

    return plans

@router.get("/api/internet-plans/{plan_id}", response_model=InternetPlanResponse | Dict[str, Any])
async def get_internet_plan_detail_endpoint(plan_id: int = Path(...), _: str = Depends(verify_api_key)):
    """
    Obtiene los detalles de un plan por ID.
    - Simple Queue: retorna nombre, precio, velocidades.
    - PPPOE: retorna nombre, precio, velocidades.
    - PCQ: retorna solo info básica (WispHub no expone endpoint de detalle para este tipo).
    """
    # Resolver tipo desde el listado en caché (evita llamada extra)
    plans = await list_internet_plans()
    plan_item = next((p for p in plans if p.plan_id == plan_id), None) if plans else None

    if not plan_item:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan_type = (plan_item.type or "").upper()

    # PCQ: WispHub no expone un endpoint de detalle para este tipo
    if plan_type == "PCQ":
        return {
            "plan_id": plan_item.plan_id,
            "name": plan_item.name,
            "type": plan_item.type,
            "note": "WispHub no expone detalles de velocidad/precio para planes PCQ."
        }

    if plan_type == "PPPOE":
        plan = await get_pppoe_plan(plan_id)
    elif plan_type == "SIMPLE QUEUE":
        plan = await get_queue_plan(plan_id)
    else:
        plan = None

    if not plan:
        raise HTTPException(status_code=404, detail="Plan details not found")

    return plan
