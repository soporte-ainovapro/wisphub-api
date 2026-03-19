from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.services.interfaces import PaymentMethodService
from app.api.deps import get_payment_method_service, verify_api_key
from app.schemas.payment_methods import PaymentMethodResponse

router = APIRouter(tags=["payment-methods"])


@router.get("/api/payment-methods/", response_model=List[PaymentMethodResponse])
async def list_payment_methods_endpoint(
    service: PaymentMethodService = Depends(get_payment_method_service),
    _: str = Depends(verify_api_key),
):
    """
    Lista todas las formas de pago configuradas en WispHub. Respuesta cacheada.
    """
    methods = await service.list_payment_methods()

    if not methods:
        raise HTTPException(
            status_code=404, detail="No se encontraron formas de pago."
        )

    return methods
