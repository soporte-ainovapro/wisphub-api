from pydantic import BaseModel


class InternetPlanResponse(BaseModel):
    name: str
    price: float
    download_speed: str
    upload_speed: str


class InternetPlanListItem(BaseModel):
    plan_id: int
    name: str
    type: str
