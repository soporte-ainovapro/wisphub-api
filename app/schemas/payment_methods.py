from pydantic import BaseModel


class PaymentMethodResponse(BaseModel):
    id: int
    name: str
