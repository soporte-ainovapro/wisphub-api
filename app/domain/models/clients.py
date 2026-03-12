from pydantic import BaseModel
   
class ClientResponse(BaseModel):
    service_id: int | None
    name: str | None
    document: str | None
    phone: str | None
    address: str | None
    city: str | None
    locality: str | None
    payment_status: str | None
    zone_id: int | None
    antenna_ip: str | None
    cut_off_date: str | None
    outstanding_balance: float | None
    lan_interface: str | None
    internet_plan_name: str | None
    internet_plan_price: float | None = None
    technician_id: int | None

class ClientUpdateRequest(BaseModel):
    """
    Campos actualizables en WispHub. Todos son opcionales; se debe enviar al menos uno.
    """
    name: str | None = None          # nombre
    last_name: str | None = None     # apellidos
    document: str | None = None      # cedula
    address: str | None = None       # direccion
    locality: str | None = None      # localidad / barrio
    city: str | None = None          # ciudad / municipio
    phone: str | None = None         # telefono (varios separados por coma)
    balance: str | None = None       # saldo (negativo = favor, positivo = deuda)

class ClientVerifyRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    internet_plan_name: str | None = None
    internet_plan_price: float | None = None

class ClientResolveRequest(BaseModel):
    """
    Recibe datos del cliente sin service_id conocido.
    Combina búsqueda + verificación en una sola llamada.
    Se requieren al menos 3 de los 4 campos.
    """
    name: str | None = None
    address: str | None = None
    internet_plan_name: str | None = None
    internet_plan_price: float | None = None

