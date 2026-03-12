from typing import Any

from fastapi import APIRouter, Depends, Path, HTTPException
from app.services.clients_service import get_client_by_document, get_client_by_phone, get_client_by_service_id, get_clients, fetch_clients_by_query, update_client_profile
from app.domain.models.responses.response_actions import ResponseAction, ClientAction
from app.domain.models.responses.response_types import ResponseType
from app.utils.responses import build_client_response
from app.domain.models.clients import ClientResponse, ClientUpdateRequest, ClientVerifyRequest, ClientResolveRequest
from app.api.dependencies import verify_api_key

router = APIRouter(tags=["Clients"])

@router.get("/api/clients/by-document/{document}", response_model=ClientResponse)
async def get_client_by_document_endpoint(document: str = Path(...), _: str = Depends(verify_api_key)):
    """
    Obtiene la información de un cliente utilizando su documento de identidad (cédula).
    Busca en el sistema de WispHub y retorna los detalles del servicio asociado.
    """
    client = await get_client_by_document(document)
    return build_client_response(client)

@router.get("/api/clients/by-phone/{phone}", response_model=ClientResponse)
async def get_client_by_phone_endpoint(phone: str = Path(...), _: str = Depends(verify_api_key)):
    """
    Obtiene la información de un cliente utilizando su número de teléfono.
    Limpia el número (remueve prefijos como '+') y realiza la búsqueda en WispHub.
    """
    client = await get_client_by_phone(phone)
    return build_client_response(client)

@router.get("/api/clients/by-service-id/{service_id}", response_model=ClientResponse)
async def get_client_by_service_id_endpoint(service_id: str = Path(...), _: str = Depends(verify_api_key)):
    """
    Obtiene la información de un cliente utilizando su ID de servicio de WispHub.
    Esta es la búsqueda más precisa ya que se utiliza el identificador único del sistema.
    """
    client = await get_client_by_service_id(service_id)
    return build_client_response(client)

@router.get("/api/clients/search", response_model=list[ClientResponse])
async def search_clients_endpoint(q: str, _: str = Depends(verify_api_key)):
    """
    Realiza una búsqueda flexible de clientes a través de un término general.
    Ideal para encontrar clientes por nombre completo, dirección, 
    o partes de palabras clave cuando no se posee la Cédula ni el Teléfono.
    """
    
    clients = await fetch_clients_by_query(q)
    return clients if clients else []

@router.get("/api/clients/", response_model=list[ClientResponse])
async def get_clients_endpoint(_: str = Depends(verify_api_key)):
    """
    Obtiene el listado general de todos los clientes activos registrados en el sistema.
    Retorna la lista parseada con los detalles esenciales de cada servicio e información de contacto.
    """
    clients = await get_clients()
    return clients if clients else []

@router.post("/api/clients/resolve", response_model=ClientResponse)
async def resolve_client_endpoint(request: ClientResolveRequest, _: str = Depends(verify_api_key)):
    """
    Identifica y verifica al cliente en una sola llamada, sin necesidad de conocer
    el service_id previamente. Busca candidatos por nombre y prueba cada uno contra
    los datos recibidos. Requiere al menos 3 de 4 campos (nombre, dirección, plan, precio).
    Útil para usuarios sin cédula ni teléfono registrado.
    """
    import re

    # --- Validar que se enviaron al menos 3 campos ---
    fields_provided = sum(
        1 for v in [request.name, request.address, request.internet_plan_name, request.internet_plan_price]
        if v is not None
    )
    if fields_provided < 3:
        raise HTTPException(
            status_code=400,
            detail="Se requieren al menos 3 campos para resolver la identidad (nombre, dirección, plan, precio)."
        )

    # --- Funciones de comparación ---
    def normalise(text: str) -> str:
        return re.sub(r'^(v/|vda/|vereda|barrio|b/)\s*', '', text.strip().lower())

    def match_string(bot_val: str | None, real_val: str | None) -> bool:
        return bool(bot_val and real_val and normalise(bot_val) in normalise(real_val))

    def score(candidate: ClientResponse, plan_price: float | None) -> int:
        points = 0
        if match_string(request.name, candidate.name):
            points += 1
        if match_string(request.address, candidate.address):
            points += 1
        if match_string(request.internet_plan_name, candidate.internet_plan_name):
            points += 1
        candidate_price = candidate.internet_plan_price
        if request.internet_plan_price is not None and candidate_price is not None:
            if abs(request.internet_plan_price - candidate_price) < 1.0:
                points += 1
        return points

    # --- Buscar candidatos por nombre (o por dirección si no hay nombre) ---
    search_query = request.name or request.address or ""
    candidates = await fetch_clients_by_query(search_query)

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron clientes con los datos proporcionados."
        )

    # --- Verificar cada candidato: todos los campos enviados deben coincidir ---
    for candidate in candidates:
        matched = score(candidate, candidate.internet_plan_price)
        if matched == fields_provided:
            return candidate

    raise HTTPException(
        status_code=404,
        detail="Ningún cliente coincide con todos los datos proporcionados."
    )

@router.put("/api/clients/{service_id}", response_model=Any)
async def update_client_endpoint(service_id: int, request: ClientUpdateRequest, _: str = Depends(verify_api_key)):
    """
    Actualiza datos críticos del perfil de un cliente en WispHub,
    tal como su número telefónico o número de documento (cédula).
    Especialmente útil cuando se enlazan usuarios sin datos estructurados previos.
    """
    
    # Solo enviar a wisphub los datos que no sean null (No sobrescribir con vacíos)
    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se brindaron datos válidos para actualizar."
        )

    # El payload a wisphub usa llaves en español
    payload = {}
    if "document" in update_data:
        payload["cedula"] = update_data["document"]
    if "phone" in update_data:
        payload["telefono"] = update_data["phone"]
    if "address" in update_data:
        payload["direccion"] = update_data["address"]

    success = await update_client_profile(service_id, payload)
    
    if success:
        return {"status": "ok", "message": "Perfil del cliente actualizado exitosamente."}
    else:
        raise HTTPException(
            status_code=400,
            detail="No se pudo actualizar el cliente. Verifique el ID."
        )

@router.post("/api/clients/{service_id}/verify", response_model=dict)
async def verify_client_identity_endpoint(service_id: int, request: ClientVerifyRequest, _: str = Depends(verify_api_key)):
    """
    Verifica la identidad del cliente tomando como base sus datos de facturación
    (como el nombre de su plan, el precio que paga, o su dirección de residencia).
    Si los datos concuerdan limpiamente, le permite continuar al Bot de WhatsApp.
    """
    from app.services.internet_plans_service import list_internet_plans, get_pppoe_plan, get_queue_plan

    client = await get_client_by_service_id(str(service_id))
    if not client:
        raise HTTPException(
            status_code=404,
            detail="El cliente especificado no fue encontrado en el sistema."
        )

    # ── Resolver el precio del plan cuando WispHub no lo devuelve en el listado ──
    internet_plan_price = client.internet_plan_price
    if internet_plan_price is None and client.internet_plan_name and request.internet_plan_price is not None:
        plans = await list_internet_plans()
        if plans:
            matched_plan = next(
                (p for p in plans if p.name.strip().upper() == client.internet_plan_name.strip().upper()),
                None
            )
            if matched_plan:
                if matched_plan.type.upper() == "PPPOE":
                    plan_detail = await get_pppoe_plan(matched_plan.plan_id)
                else:
                    plan_detail = await get_queue_plan(matched_plan.plan_id)
                if plan_detail:
                    internet_plan_price = plan_detail.price

    matched_fields = []

    def normalise(text: str) -> str:
        """Elimina prefijos comunes en direcciones de WispHub (V/, VDA/, etc.)."""
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

    # Requerir al menos 3 de los 4 campos posibles
    request_fields_count = sum(
        1 for v in [request.name, request.address, request.internet_plan_name, request.internet_plan_price]
        if v is not None
    )

    if request_fields_count < 3:
        raise HTTPException(
            status_code=400,
            detail="Se requieren al menos 3 campos para verificar la identidad (nombre, dirección, plan, precio)."
        )

    # Válido solo si TODOS los campos enviados coinciden
    is_valid = (len(matched_fields) == request_fields_count)

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
            "message": "Los datos proporcionados no coinciden con la información registrada."
        }