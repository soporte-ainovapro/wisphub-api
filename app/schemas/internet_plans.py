from typing import Optional

from pydantic import BaseModel


class InternetPlanResponse(BaseModel):
    name: str
    price: Optional[float] = None
    download_speed: Optional[str] = None
    upload_speed: Optional[str] = None


class InternetPlanPCQResponse(BaseModel):
    plan_id: int
    name: str
    type: str
    note: str


class InternetPlanListItem(BaseModel):
    plan_id: int
    name: str
    type: str
