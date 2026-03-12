from fastapi import APIRouter, Depends, Path, HTTPException
from typing import List, Dict, Any

from app.infrastructure.gateways.wisphub_internet_plan_gateway import WispHubInternetPlanGateway
from app.domain.models.responses.response_actions import PlanAction
from app.domain.models.internet_plans import InternetPlanListItem, InternetPlanResponse
from app.api.dependencies import verify_api_key
from app.core.config import settings

router = APIRouter(tags=["internet-plans"])


def get_plan_gateway() -> WispHubInternetPlanGateway:
    return WispHubInternetPlanGateway(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )


@router.get("/api/internet-plans/", response_model=List[InternetPlanListItem])
async def list_internet_plans_endpoint(
    gateway: WispHubInternetPlanGateway = Depends(get_plan_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Lista todos los planes de internet configurados en WispHub. Respuesta cacheada.
    """
    plans = await gateway.list_internet_plans()

    if not plans:
        raise HTTPException(status_code=404, detail="No se encontraron planes de internet.")

    return plans


@router.get("/api/internet-plans/{plan_id}", response_model=InternetPlanResponse | Dict[str, Any])
async def get_internet_plan_detail_endpoint(
    plan_id: int = Path(...),
    gateway: WispHubInternetPlanGateway = Depends(get_plan_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene los detalles de un plan por ID (PPPOE, Simple Queue, PCQ).
    """
    plans = await gateway.list_internet_plans()
    plan_item = next((p for p in plans if p.plan_id == plan_id), None) if plans else None

    if not plan_item:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan_type = (plan_item.type or "").upper()

    if plan_type == "PCQ":
        return {
            "plan_id": plan_item.plan_id,
            "name": plan_item.name,
            "type": plan_item.type,
            "note": "WispHub no expone detalles de velocidad/precio para planes PCQ.",
        }

    if plan_type == "PPPOE":
        plan = await gateway.get_pppoe_plan(plan_id)
    elif plan_type == "SIMPLE QUEUE":
        plan = await gateway.get_queue_plan(plan_id)
    else:
        plan = None

    if not plan:
        raise HTTPException(status_code=404, detail="Plan details not found")

    return plan
