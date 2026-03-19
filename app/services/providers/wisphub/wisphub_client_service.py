"""
Servicio WispHub para clientes.

Combina acceso HTTP a la API de WispHub con la lógica de negocio:
scoring de resolución de identidad, verificación de campos y mapeo
de nombres Python → WispHub.
"""

import re
from typing import Any, Dict, List, Optional

import httpx
from async_lru import alru_cache
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.clients import (
    ClientResponse,
    ClientResolveRequest,
    ClientVerifyRequest,
)
from app.schemas.internet_plans import InternetPlanListItem, InternetPlanResponse

# Mapeo de nombres de campo Python → nombres de campo WispHub
FIELD_MAP: Dict[str, str] = {
    "name": "nombre",
    "last_name": "apellidos",
    "document": "cedula",
    "address": "direccion",
    "locality": "localidad",
    "city": "ciudad",
    "phone": "telefono",
    "balance": "saldo",
}


def _normalise(text: str) -> str:
    return re.sub(r"^(v/|vda/|vereda|barrio|b/)\s*", "", text.strip().lower())


def _match_string(bot_val: Optional[str], real_val: Optional[str]) -> bool:
    if bot_val and real_val:
        return _normalise(bot_val) in _normalise(real_val)
    return False


def _parse_client(c: dict) -> ClientResponse:
    zone = c.get("zona")
    technician = c.get("tecnico")
    internet_plan = c.get("plan_internet")

    raw_price = c.get("precio_plan")
    try:
        resolved_price = (
            float(raw_price) if raw_price not in (None, "", "0", "0.00") else None
        )
    except (ValueError, TypeError):
        resolved_price = None

    return ClientResponse(
        service_id=c.get("id_servicio"),
        name=c.get("nombre"),
        document=c.get("cedula"),
        phone=c.get("telefono"),
        address=c.get("direccion"),
        city=c.get("ciudad"),
        locality=c.get("localidad"),
        payment_status=c.get("estado"),
        zone_id=zone.get("id") if isinstance(zone, dict) else None,
        antenna_ip=c.get("ip"),
        cut_off_date=c.get("fecha_corte"),
        outstanding_balance=c.get("saldo"),
        lan_interface=c.get("interfaz_lan"),
        internet_plan_name=(
            internet_plan.get("nombre") if isinstance(internet_plan, dict) else None
        ),
        internet_plan_price=resolved_price,
        technician_id=(technician.get("id") if isinstance(technician, dict) else None),
    )


class WispHubClientService:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.headers = {"Authorization": f"Api-Key {api_key}"}

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def fetch_client(self, params: Dict[str, str]) -> Optional[ClientResponse]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/api/clientes/",
                headers=self.headers,
                params=params,
            )

        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        results = data.get("results")
        if not isinstance(results, list) or not results:
            return None

        return _parse_client(results[0])

    async def fetch_clients_by_query(self, query: str) -> List[ClientResponse]:
        all_clients = await self.get_clients()
        if not all_clients:
            return []

        q = query.strip().lower()
        return [
            c
            for c in all_clients
            if q
            in " ".join(filter(None, [c.name, c.address, c.document, c.phone])).lower()
        ]

    async def get_client_by_document(self, document: str) -> Optional[ClientResponse]:
        return await self.fetch_client({"cedula": document})

    async def get_client_by_phone(self, phone: str) -> Optional[ClientResponse]:
        return await self.fetch_client({"telefono": phone.replace("+", "").strip()})

    async def get_client_by_service_id(
        self, service_id: str
    ) -> Optional[ClientResponse]:
        return await self.fetch_client({"id_servicio": service_id})

    @alru_cache(maxsize=1, ttl=300)
    async def get_clients(self) -> List[ClientResponse]:
        """Carga todos los clientes paginando. Resultado cacheado 5 min."""
        all_results: List[ClientResponse] = []
        next_url: Optional[str] = f"{self.base_url}/api/clientes/"

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            while next_url:
                response = await client.get(next_url, headers=self.headers)
                if response.status_code != 200:
                    break
                try:
                    data = response.json()
                except Exception:
                    break
                results = data.get("results")
                if not isinstance(results, list):
                    break
                all_results.extend(_parse_client(c) for c in results)
                next_url = data.get("next")

        return all_results

    async def update_client_profile(self, service_id: int, request_data: dict) -> bool:
        url = f"{self.base_url}/api/clientes/{service_id}/perfil/"
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.put(
                    url, headers=self.headers, json=request_data
                )
                return response.status_code in [200, 204]
            except httpx.RequestError:
                return False

    async def _list_internet_plans(
        self,
    ) -> Optional[List[InternetPlanListItem]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/api/plan-internet/",
                headers=self.headers,
            )
        if response.status_code != 200:
            return None
        data = response.json()
        results = data.get("results")
        if not isinstance(results, list):
            return None
        return [
            InternetPlanListItem(
                plan_id=p.get("id"),
                name=p.get("nombre"),
                type=p.get("tipo"),
            )
            for p in results
        ]

    async def _get_plan_detail(
        self, endpoint: str, plan_id: int
    ) -> Optional[InternetPlanResponse]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}{plan_id}/",
                headers=self.headers,
            )
        if response.status_code != 200:
            return None
        plan = response.json()
        if not isinstance(plan, dict) or not plan:
            return None
        return InternetPlanResponse(
            name=plan.get("nombre"),
            price=plan.get("precio"),
            download_speed=plan.get("bajada"),
            upload_speed=plan.get("subida"),
        )

    # ------------------------------------------------------------------
    # Business logic
    # ------------------------------------------------------------------

    async def get_by_document(self, document: str) -> Optional[ClientResponse]:
        return await self.get_client_by_document(document)

    async def get_by_phone(self, phone: str) -> Optional[ClientResponse]:
        return await self.get_client_by_phone(phone)

    async def get_by_service_id(self, service_id: str) -> Optional[ClientResponse]:
        return await self.get_client_by_service_id(service_id)

    async def search(self, query: str) -> List[ClientResponse]:
        return await self.fetch_clients_by_query(query)

    async def get_all(self) -> List[ClientResponse]:
        return await self.get_clients()

    async def resolve(self, request: ClientResolveRequest) -> ClientResponse:
        """
        Identifica al cliente a partir de al menos 3 de 4 campos de contexto:
        nombre, dirección, plan de internet y precio del plan.
        """
        fields_provided = sum(
            1
            for v in [
                request.name,
                request.address,
                request.internet_plan_name,
                request.internet_plan_price,
            ]
            if v is not None
        )
        if fields_provided < 3:
            raise HTTPException(
                status_code=400,
                detail="Se requieren al menos 3 campos para resolver la identidad (nombre, dirección, plan, precio).",
            )

        def _score(candidate: ClientResponse) -> int:
            points = 0
            if _match_string(request.name, candidate.name):
                points += 1
            if _match_string(request.address, candidate.address):
                points += 1
            if _match_string(request.internet_plan_name, candidate.internet_plan_name):
                points += 1
            if (
                request.internet_plan_price is not None
                and candidate.internet_plan_price is not None
                and abs(request.internet_plan_price - candidate.internet_plan_price)
                < 1.0
            ):
                points += 1
            return points

        search_query = request.name or request.address or ""
        candidates = await self.fetch_clients_by_query(search_query)

        if not candidates:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron clientes con los datos proporcionados.",
            )

        for candidate in candidates:
            if _score(candidate) == fields_provided:
                return candidate

        raise HTTPException(
            status_code=404,
            detail="Ningún cliente coincide con todos los datos proporcionados.",
        )

    async def verify(
        self, service_id: int, request: ClientVerifyRequest
    ) -> Dict[str, Any]:
        """
        Verifica la identidad del cliente comparando los campos proporcionados
        con los datos reales almacenados en WispHub.
        """
        request_fields_count = sum(
            1
            for v in [
                request.name,
                request.address,
                request.internet_plan_name,
                request.internet_plan_price,
            ]
            if v is not None
        )
        if request_fields_count < 3:
            raise HTTPException(
                status_code=400,
                detail="Se requieren al menos 3 campos para verificar la identidad (nombre, dirección, plan, precio).",
            )

        client = await self.get_client_by_service_id(str(service_id))
        if not client:
            raise HTTPException(
                status_code=404,
                detail="El cliente especificado no fue encontrado en el sistema.",
            )

        # Intentar resolver el precio del plan si no está en el cliente
        internet_plan_price = client.internet_plan_price
        if (
            internet_plan_price is None
            and client.internet_plan_name
            and request.internet_plan_price is not None
        ):
            plans = await self._list_internet_plans()
            if plans:
                matched_plan = next(
                    (
                        p
                        for p in plans
                        if p.name.strip().upper()
                        == client.internet_plan_name.strip().upper()
                    ),
                    None,
                )
                if matched_plan:
                    if matched_plan.type.upper() == "PPPOE":
                        plan_detail = await self._get_plan_detail(
                            "/api/plan-internet/pppoe/", matched_plan.plan_id
                        )
                    else:
                        plan_detail = await self._get_plan_detail(
                            "/api/plan-internet/queue/", matched_plan.plan_id
                        )
                    if plan_detail:
                        internet_plan_price = plan_detail.price

        matched_fields = []
        if _match_string(request.name, client.name):
            matched_fields.append("name")
        if _match_string(request.address, client.address):
            matched_fields.append("address")
        if _match_string(request.internet_plan_name, client.internet_plan_name):
            matched_fields.append("internet_plan_name")
        if request.internet_plan_price is not None and internet_plan_price is not None:
            if abs(request.internet_plan_price - internet_plan_price) < 1.0:
                matched_fields.append("internet_plan_price")

        is_valid = len(matched_fields) == request_fields_count

        if is_valid:
            return {
                "is_valid": True,
                "matched_fields": matched_fields,
                "message": "Identidad validada de manera exitosa.",
            }

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

    async def update(self, service_id: int, update_data: Dict[str, Any]) -> bool:
        """Traduce los nombres de campo Python al esquema de WispHub y persiste."""
        payload = {FIELD_MAP[k]: v for k, v in update_data.items() if k in FIELD_MAP}
        return await self.update_client_profile(service_id, payload)
