import httpx
from typing import List, Optional, Dict, Any
from async_lru import alru_cache
from app.core.config import settings
from app.schemas.clients import ClientResponse

HEADERS = {
    "Authorization": f"Api-Key {settings.WISPHUB_NET_KEY}"
}

def parse_client(c: dict) -> ClientResponse:
    zone = c.get("zona")
    technician = c.get("tecnico")
    internet_plan = c.get("plan_internet")

    # precio_plan is a top-level string field always present in WispHub list responses
    # (e.g. "40000.00"). plan_internet.precio is NOT populated in list responses.
    raw_price = c.get("precio_plan")
    try:
        resolved_price = float(raw_price) if raw_price not in (None, "", "0", "0.00") else None
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
            internet_plan.get("nombre")
            if isinstance(internet_plan, dict)
            else None
        ),
        internet_plan_price=resolved_price,
        technician_id=(
            technician.get("id")
            if isinstance(technician, dict)
            else None
        ),
    )

async def fetch_client(params: Dict[str, str]) -> Optional[ClientResponse]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            settings.CLIENTS_URL,
            headers=HEADERS,
            params=params
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

    return parse_client(results[0])

async def fetch_clients_by_query(query: str) -> List[ClientResponse]:
    """
    Búsqueda flexible contra el pool de clientes en caché.
    Filtra localmente por nombre, dirección, documento y teléfono
    (caso insensible, búsqueda parcial).
    El parámetro 'search' de WispHub no filtra realmente — devuelve
    todos los registros sin importar el valor enviado.
    """
    all_clients = await get_clients()
    if not all_clients:
        return []

    q = query.strip().lower()
    matches: List[ClientResponse] = []
    for c in all_clients:
        searchable = " ".join(filter(None, [
            c.name,
            c.address,
            c.document,
            c.phone,
        ])).lower()
        if q in searchable:
            matches.append(c)

    return matches

async def get_client_by_document(document: str) -> Optional[ClientResponse]:
    return await fetch_client({"cedula": document})

async def get_client_by_phone(phone: str) -> Optional[ClientResponse]:
    phone = phone.replace("+", "").strip()
    return await fetch_client({"telefono": phone})

async def get_client_by_service_id(service_id: str) -> Optional[ClientResponse]:
    return await fetch_client({"id_servicio": service_id})

@alru_cache(maxsize=1, ttl=300)
async def get_clients() -> List[ClientResponse]:
    """
    Carga TODOS los clientes de WispHub siguiendo la paginación.
    Los resultados se cachean por 5 minutos para evitar carga repetida.
    """
    all_results: List[ClientResponse] = []
    next_url: Optional[str] = settings.CLIENTS_URL

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        while next_url:
            response = await client.get(next_url, headers=HEADERS)
            if response.status_code != 200:
                break
            try:
                data = response.json()
            except Exception:
                break
            results = data.get("results")
            if not isinstance(results, list):
                break
            all_results.extend(parse_client(c) for c in results)
            next_url = data.get("next")  # None cuando no hay más páginas

    return all_results

async def update_client_profile(service_id: int, request_data: dict) -> bool:
    """
    Actualiza el perfil de un cliente en WispHub (ej. Cédula o Teléfono).
    Endpoint externo: PUT o PATCH https://api.wisphub.net/api/clientes/{id_servicio}/perfil/
    """
    url = f"{settings.WISPHUB_NET_HOST}/api/clientes/{service_id}/perfil/"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.patch(
                url,
                headers=HEADERS,
                json=request_data
            )
            # Retornar True si el status code denota éxito en creación o actualización.
            return response.status_code in [200, 204]
        except httpx.RequestError:
            return False