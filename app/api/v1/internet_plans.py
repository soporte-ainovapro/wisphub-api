from fastapi import APIRouter, Path

from app.schemas.responses.backend_response import BackendResponse
from app.schemas.responses.response_actions import ResponseAction, PlanAction
from app.schemas.responses.response_types import ResponseType
from app.schemas.internet_plans import InternetPlanListItem, InternetPlanResponse
from typing import List, Dict, Any
from app.services.internet_plans_service import get_plan_type, get_queue_plan, list_internet_plans, get_pppoe_plan

router = APIRouter(tags=["internet-plans"])

@router.get("/api/v1/internet-plans/", response_model=BackendResponse[List[InternetPlanListItem]])
async def list_internet_plans_endpoint():
    """
    Lista todos los planes de internet configurados en el sistema WispHub.
    Esta consulta está cacheada internamente para mejorar el rendimiento y evitar
    llamadas redundantes continuas a la API externa.
    """
    plans = await list_internet_plans()

    if not plans:
        return BackendResponse.info(
            action=PlanAction.NOT_FOUND
        )

    return BackendResponse.success(
        action=PlanAction.LISTED,
        data=plans
    )

@router.get("/api/v1/internet-plans/{plan_id}", response_model=BackendResponse[InternetPlanResponse | Dict[str, Any]])
async def get_internet_plan_detail_endpoint(plan_id: int = Path(...)):
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
        return BackendResponse.info(action=PlanAction.NOT_FOUND)

    plan_type = (plan_item.type or "").upper()

    # PCQ: WispHub no expone un endpoint de detalle para este tipo
    if plan_type == "PCQ":
        return BackendResponse.success(
            action=PlanAction.FOUND,
            data={
                "plan_id": plan_item.plan_id,
                "name": plan_item.name,
                "type": plan_item.type,
                "note": "WispHub no expone detalles de velocidad/precio para planes PCQ."
            }
        )

    if plan_type == "PPPOE":
        plan = await get_pppoe_plan(plan_id)
    elif plan_type == "SIMPLE QUEUE":
        plan = await get_queue_plan(plan_id)
    else:
        plan = None

    if not plan:
        return BackendResponse.info(action=PlanAction.NOT_FOUND)

    return BackendResponse.success(
        action=PlanAction.FOUND,
        data=plan
    )
