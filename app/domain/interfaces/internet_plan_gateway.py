from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.internet_plans import InternetPlanResponse, InternetPlanListItem

class IInternetPlanGateway(ABC):
    @abstractmethod
    async def list_internet_plans(self) -> List[InternetPlanResponse]:
        pass

    @abstractmethod
    async def get_pppoe_plan(self, plan_id: int) -> Optional[InternetPlanResponse]:
        pass

    @abstractmethod
    async def get_queue_plan(self, plan_id: int) -> Optional[InternetPlanResponse]:
        pass
