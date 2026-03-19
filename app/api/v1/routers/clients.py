from fastapi import APIRouter, Depends, Path, HTTPException
from typing import Dict, List

from app.services.interfaces import ClientService
from app.api.deps import get_client_service, verify_api_key
from app.schemas.clients import (
    ClientResponse,
    ClientUpdateRequest,
    ClientVerifyRequest,
    ClientResolveRequest,
)
from app.utils.responses import build_client_response

router = APIRouter(tags=["Clients"])


@router.get("/api/clients/by-document/{document}", response_model=ClientResponse)
async def get_client_by_document_endpoint(
    document: str = Path(...),
    service: ClientService = Depends(get_client_service),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene la información de un cliente utilizando su documento de identidad (cédula).
    """
    client = await service.get_by_document(document)
    return build_client_response(client)


@router.get("/api/clients/by-phone/{phone}", response_model=ClientResponse)
async def get_client_by_phone_endpoint(
    phone: str = Path(...),
    service: ClientService = Depends(get_client_service),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene la información de un cliente utilizando su número de teléfono.
    """
    client = await service.get_by_phone(phone)
    return build_client_response(client)


@router.get("/api/clients/by-service-id/{service_id}", response_model=ClientResponse)
async def get_client_by_service_id_endpoint(
    service_id: str = Path(...),
    service: ClientService = Depends(get_client_service),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene la información de un cliente utilizando su ID de servicio de WispHub.
    """
    client = await service.get_by_service_id(service_id)
    return build_client_response(client)


@router.get("/api/clients/search", response_model=List[ClientResponse])
async def search_clients_endpoint(
    q: str,
    service: ClientService = Depends(get_client_service),
    _: str = Depends(verify_api_key),
):
    """
    Realiza una búsqueda flexible de clientes a través de un término general.
    """
    clients = await service.search(q)
    return clients if clients else []


@router.get("/api/clients/", response_model=List[ClientResponse])
async def get_clients_endpoint(
    service: ClientService = Depends(get_client_service),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene el listado general de todos los clientes activos en el sistema.
    """
    clients = await service.get_all()
    return clients if clients else []


@router.post("/api/clients/resolve", response_model=ClientResponse)
async def resolve_client_endpoint(
    request: ClientResolveRequest,
    service: ClientService = Depends(get_client_service),
    _: str = Depends(verify_api_key),
):
    """
    Identifica y verifica al cliente en una sola llamada. Requiere al menos 3 de 4 campos.
    """
    return await service.resolve(request)


@router.put("/api/clients/{service_id}", response_model=Dict[str, str])
async def update_client_endpoint(
    service_id: int,
    request: ClientUpdateRequest,
    service: ClientService = Depends(get_client_service),
    _: str = Depends(verify_api_key),
):
    """
    Actualiza datos críticos del perfil de un cliente en WispHub.
    """
    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=400, detail="No se brindaron datos válidos para actualizar."
        )

    success = await service.update(service_id, update_data)

    if success:
        return {
            "status": "ok",
            "message": "Perfil del cliente actualizado exitosamente.",
        }
    else:
        raise HTTPException(
            status_code=400, detail="No se pudo actualizar el cliente. Verifique el ID."
        )


@router.post("/api/clients/{service_id}/verify", response_model=dict)
async def verify_client_identity_endpoint(
    service_id: int,
    request: ClientVerifyRequest,
    service: ClientService = Depends(get_client_service),
    _: str = Depends(verify_api_key),
):
    """
    Verifica la identidad del cliente por sus datos de facturación.
    """
    return await service.verify(service_id, request)
