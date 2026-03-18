from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.invoices import InvoiceResponse


class IInvoiceGateway(ABC):
    @abstractmethod
    async def get_invoices(self) -> List[InvoiceResponse]:
        pass

    @abstractmethod
    async def get_invoice(self, invoice_id: int) -> Optional[InvoiceResponse]:
        pass

    