import httpx
from typing import List, Dict, Any, Optional
from async_lru import alru_cache
from app.core.config import settings
from app.schemas.internet_plans import InternetPlanResponse, InternetPlanListItem

HEADERS = {"Authorization": f"Api-Key {settings.WISPHUB_NET_KEY}"}

async def _get_plan_detail(
    base_url: str,
    plan_id: int
) -> Optional[InternetPlanResponse]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{base_url}{plan_id}/",
            headers=HEADERS
        )

    if response.status_code != 200:
        return None

    plan = response.json()

    if not isinstance(plan, dict) or not plan:
        return None

    p = plan
    
    return InternetPlanResponse(
        name=p.get("nombre"),
        price=p.get("precio"),
        download_speed=p.get("bajada"),
        upload_speed=p.get("subida"),
    )

@alru_cache(maxsize=32, ttl=900)
async def list_internet_plans() -> Optional[List[InternetPlanListItem]]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(settings.PLANS_URL, headers=HEADERS)
        
    if response.status_code != 200:
        return None

    data = response.json()
    results = data.get("results")
       
    if not isinstance(results, list):
        return None

    return [
        InternetPlanListItem(
            plan_id=plan.get("id"),
            name=plan.get("nombre"),
            type=plan.get("tipo"),
        )
        for plan in results
    ]

async def get_plan_type(plan_id: int) -> Optional[str]:
    plans = await list_internet_plans()
    
    if not plans:
        return None
        
    for plan in plans:
        if plan.plan_id == plan_id:
            return plan.type

    return None


async def get_pppoe_plan(plan_id: int) -> Optional[Dict[str, Any]]:
    return await _get_plan_detail(settings.PLANS_PPPOE_URL, plan_id)


async def get_queue_plan(plan_id: int) -> Optional[Dict[str, Any]]:
    return await _get_plan_detail(settings.PLANS_QUEUE_URL, plan_id)
