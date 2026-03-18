from abc import ABC, abstractmethod
from typing import List
from app.domain.models.payment_methods import PaymentMethodResponse

class IPaymentMethodGateway(ABC):
    @abstractmethod
    async def get_payment_methods(self) -> List[PaymentMethodResponse]:
        pass