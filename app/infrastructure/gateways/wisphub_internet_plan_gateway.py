import httpx
from typing import List, Optional
from async_lru import alru_cache

from app.domain.interfaces.internet_plan_gateway import IInternetPlanGateway
from app.domain.models.internet_plans import InternetPlanResponse, InternetPlanListItem


class WispHubInternetPlanGateway(IInternetPlanGateway):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Api-Key {api_key}"}

    async def _get_plan_detail(self, endpoint: str, plan_id: int) -> Optional[InternetPlanResponse]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}{plan_id}/",
                headers=self.headers,
            )

        if response.status_code != 200:
            return None

        plan = response.json()
        if not isinstance(plan, dict) or not plan:
            return None

        return InternetPlanResponse(
            name=plan.get("nombre"),
            price=plan.get("precio"),
            download_speed=plan.get("bajada"),
            upload_speed=plan.get("subida"),
        )

    @alru_cache(ttl=900)
    async def list_internet_plans(self) -> Optional[List[InternetPlanListItem]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/api/plan-internet/",
                headers=self.headers,
            )

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

    async def get_pppoe_plan(self, plan_id: int) -> Optional[InternetPlanResponse]:
        return await self._get_plan_detail("/api/plan-internet/pppoe/", plan_id)

    async def get_queue_plan(self, plan_id: int) -> Optional[InternetPlanResponse]:
        return await self._get_plan_detail("/api/plan-internet/queue/", plan_id)
