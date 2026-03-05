from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import clients, tickets, network, internet_plans, auth
from app.schemas.responses.backend_response import BackendResponse
from app.schemas.responses.response_actions import SystemAction
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.exception_handlers import validation_exception_handler, http_exception_handler, general_exception_handler

app = FastAPI(
    title="WispHub API",
    description="API de integración local con WispHub.",
    version="1.0.0"
)

# Configuración de CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://127.0.0.1:8082",
    "null", # Permite acceso desde archivos locales (file://)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["system"], response_model=BackendResponse[dict])
async def health_check():
    """
    Ruta de comprobación del estado de salud (Health Check).
    Utilizado por balanceadores de carga y Docker para confirmar
    que el servidor está levantado y aceptando conexiones.
    (Public endpoint — no authentication required.)
    """
    return BackendResponse.success(action=SystemAction.HEALTH_OK, data={"status": "ok", "service": "WispHub Local API"})

# Registrar manejadores de excepciones globales
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Public: Authentication
app.include_router(auth.router)

# Protected: Business logic routers
app.include_router(clients.router)
app.include_router(tickets.router)
app.include_router(network.router)
app.include_router(internet_plans.router)