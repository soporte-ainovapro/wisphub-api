"""
Servicio WispHub para planes de internet.

Combina acceso HTTP a la API de WispHub con la lógica de negocio:
listado de planes y obtención de detalles según tipo (PPPOE, Simple Queue, PCQ).
"""

from typing import Any, List, Optional

import httpx
from async_lru import alru_cache
from fastapi import HTTPException

from app.schemas.internet_plans import InternetPlanListItem, InternetPlanResponse


class WispHubInternetPlanService:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.headers = {"Authorization": f"Api-Key {api_key}"}

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    @alru_cache(ttl=900)
    async def list_internet_plans(self) -> Optional[List[InternetPlanListItem]]:
        """Lista todos los planes de internet. Resultado cacheado 15 min."""
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
                plan_id=p.get("id"),
                name=p.get("nombre"),
                type=p.get("tipo"),
            )
            for p in results
        ]

    @alru_cache(ttl=900)
    async def get_pppoe_plan(self, plan_id: int) -> Optional[InternetPlanResponse]:
        return await self._get_plan_detail("/api/plan-internet/pppoe/", plan_id)

    @alru_cache(ttl=900)
    async def get_queue_plan(self, plan_id: int) -> Optional[InternetPlanResponse]:
        return await self._get_plan_detail("/api/plan-internet/queue/", plan_id)

    async def _get_plan_detail(
        self, endpoint: str, plan_id: int
    ) -> Optional[InternetPlanResponse]:
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

    # ------------------------------------------------------------------
    # Business logic
    # ------------------------------------------------------------------

    async def list_plans(self) -> Optional[List[InternetPlanListItem]]:
        return await self.list_internet_plans()

    async def get_plan_detail(self, plan_id: int) -> Any:
        plans = await self.list_internet_plans()
        plan_item = (
            next((p for p in plans if p.plan_id == plan_id), None) if plans else None
        )

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
            plan = await self.get_pppoe_plan(plan_id)
        elif plan_type == "SIMPLE QUEUE":
            plan = await self.get_queue_plan(plan_id)
        else:
            plan = None

        if not plan:
            raise HTTPException(status_code=404, detail="Plan details not found")

        return plan
