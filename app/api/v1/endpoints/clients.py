from typing import Any, List

from fastapi import APIRouter, Depends, Path, HTTPException
from app.infrastructure.gateways.wisphub_client_gateway import WispHubClientGateway
from app.domain.models.responses.response_actions import ResponseAction, ClientAction
from app.domain.models.responses.response_types import ResponseType
from app.utils.responses import build_client_response
from app.domain.models.clients import ClientResponse, ClientUpdateRequest, ClientVerifyRequest, ClientResolveRequest
from app.api.dependencies import verify_api_key
from app.core.config import settings

router = APIRouter(tags=["Clients"])


def get_client_gateway() -> WispHubClientGateway:
    return WispHubClientGateway(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )


@router.get("/api/clients/by-document/{document}", response_model=ClientResponse)
async def get_client_by_document_endpoint(
    document: str = Path(...),
    gateway: WispHubClientGateway = Depends(get_client_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene la información de un cliente utilizando su documento de identidad (cédula).
    """
    client = await gateway.get_client_by_document(document)
    return build_client_response(client)


@router.get("/api/clients/by-phone/{phone}", response_model=ClientResponse)
async def get_client_by_phone_endpoint(
    phone: str = Path(...),
    gateway: WispHubClientGateway = Depends(get_client_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene la información de un cliente utilizando su número de teléfono.
    """
    client = await gateway.get_client_by_phone(phone)
    return build_client_response(client)


@router.get("/api/clients/by-service-id/{service_id}", response_model=ClientResponse)
async def get_client_by_service_id_endpoint(
    service_id: str = Path(...),
    gateway: WispHubClientGateway = Depends(get_client_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene la información de un cliente utilizando su ID de servicio de WispHub.
    """
    client = await gateway.get_client_by_service_id(service_id)
    return build_client_response(client)


@router.get("/api/clients/search", response_model=List[ClientResponse])
async def search_clients_endpoint(
    q: str,
    gateway: WispHubClientGateway = Depends(get_client_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Realiza una búsqueda flexible de clientes a través de un término general.
    """
    clients = await gateway.fetch_clients_by_query(q)
    return clients if clients else []


@router.get("/api/clients/", response_model=List[ClientResponse])
async def get_clients_endpoint(
    gateway: WispHubClientGateway = Depends(get_client_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene el listado general de todos los clientes activos en el sistema.
    """
    clients = await gateway.get_clients()
    return clients if clients else []


@router.post("/api/clients/resolve", response_model=ClientResponse)
async def resolve_client_endpoint(
    request: ClientResolveRequest,
    gateway: WispHubClientGateway = Depends(get_client_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Identifica y verifica al cliente en una sola llamada. Requiere al menos 3 de 4 campos.
    """
    import re

    fields_provided = sum(
        1 for v in [request.name, request.address, request.internet_plan_name, request.internet_plan_price]
        if v is not None
    )
    if fields_provided < 3:
        raise HTTPException(
            status_code=400,
            detail="Se requieren al menos 3 campos para resolver la identidad (nombre, dirección, plan, precio).",
        )

    def normalise(text: str) -> str:
        return re.sub(r'^(v/|vda/|vereda|barrio|b/)\s*', '', text.strip().lower())

    def match_string(bot_val: str | None, real_val: str | None) -> bool:
        return bool(bot_val and real_val and normalise(bot_val) in normalise(real_val))

    def score(candidate: ClientResponse) -> int:
        points = 0
        if match_string(request.name, candidate.name):
            points += 1
        if match_string(request.address, candidate.address):
            points += 1
        if match_string(request.internet_plan_name, candidate.internet_plan_name):
            points += 1
        if request.internet_plan_price is not None and candidate.internet_plan_price is not None:
            if abs(request.internet_plan_price - candidate.internet_plan_price) < 1.0:
                points += 1
        return points

    search_query = request.name or request.address or ""
    candidates = await gateway.fetch_clients_by_query(search_query)

    if not candidates:
        raise HTTPException(status_code=404, detail="No se encontraron clientes con los datos proporcionados.")

    for candidate in candidates:
        if score(candidate) == fields_provided:
            return candidate

    raise HTTPException(status_code=404, detail="Ningún cliente coincide con todos los datos proporcionados.")


@router.put("/api/clients/{service_id}", response_model=Any)
async def update_client_endpoint(
    service_id: int,
    request: ClientUpdateRequest,
    gateway: WispHubClientGateway = Depends(get_client_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Actualiza datos críticos del perfil de un cliente en WispHub.
    """
    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No se brindaron datos válidos para actualizar.")

    # Map our field names → WispHub API field names
    field_map = {
        "name":      "nombre",
        "last_name": "apellidos",
        "document":  "cedula",
        "address":   "direccion",
        "locality":  "localidad",
        "city":      "ciudad",
        "phone":     "telefono",
        "balance":   "saldo",
    }
    payload = {field_map[k]: v for k, v in update_data.items() if k in field_map}

    success = await gateway.update_client_profile(service_id, payload)

    if success:
        return {"status": "ok", "message": "Perfil del cliente actualizado exitosamente."}
    else:
        raise HTTPException(status_code=400, detail="No se pudo actualizar el cliente. Verifique el ID.")


@router.post("/api/clients/{service_id}/verify", response_model=dict)
async def verify_client_identity_endpoint(
    service_id: int,
    request: ClientVerifyRequest,
    gateway: WispHubClientGateway = Depends(get_client_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Verifica la identidad del cliente por sus datos de facturación.
    """
    from app.infrastructure.gateways.wisphub_internet_plan_gateway import WispHubInternetPlanGateway

    client = await gateway.get_client_by_service_id(str(service_id))
    if not client:
        raise HTTPException(status_code=404, detail="El cliente especificado no fue encontrado en el sistema.")

    internet_plan_price = client.internet_plan_price
    if internet_plan_price is None and client.internet_plan_name and request.internet_plan_price is not None:
        plan_gateway = WispHubInternetPlanGateway(
            base_url=settings.WISPHUB_NET_HOST,
            api_key=settings.WISPHUB_NET_KEY,
        )
        plans = await plan_gateway.list_internet_plans()
        if plans:
            matched_plan = next(
                (p for p in plans if p.name.strip().upper() == client.internet_plan_name.strip().upper()),
                None,
            )
            if matched_plan:
                if matched_plan.type.upper() == "PPPOE":
                    plan_detail = await plan_gateway.get_pppoe_plan(matched_plan.plan_id)
                else:
                    plan_detail = await plan_gateway.get_queue_plan(matched_plan.plan_id)
                if plan_detail:
                    internet_plan_price = plan_detail.price

    matched_fields = []

    def normalise(text: str) -> str:
        import re
        return re.sub(r'^(v/|vda/|vereda|barrio|b/)\s*', '', text.strip().lower())

    def match_string(bot_val: str | None, real_val: str | None) -> bool:
        if bot_val and real_val:
            return normalise(bot_val) in normalise(real_val)
        return False

    if match_string(request.name, client.name):
        matched_fields.append("name")
    if match_string(request.address, client.address):
        matched_fields.append("address")
    if match_string(request.internet_plan_name, client.internet_plan_name):
        matched_fields.append("internet_plan_name")
    if request.internet_plan_price is not None and internet_plan_price is not None:
        if abs(request.internet_plan_price - internet_plan_price) < 1.0:
            matched_fields.append("internet_plan_price")

    request_fields_count = sum(
        1 for v in [request.name, request.address, request.internet_plan_name, request.internet_plan_price]
        if v is not None
    )

    if request_fields_count < 3:
        raise HTTPException(
            status_code=400,
            detail="Se requieren al menos 3 campos para verificar la identidad (nombre, dirección, plan, precio).",
        )

    is_valid = len(matched_fields) == request_fields_count

    if is_valid:
        return {"is_valid": True, "matched_fields": matched_fields, "message": "Identidad validada de manera exitosa."}
    else:
        return {
            "is_valid": False,
            "matched_fields": matched_fields,
            "debug": {
                "client_address": client.address,
                "client_plan_name": client.internet_plan_name,
                "resolved_plan_price": internet_plan_price,
            },
            "message": "Los datos proporcionados no coinciden con la información registrada.",
        }
