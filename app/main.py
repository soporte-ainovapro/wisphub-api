from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import clients, tickets, network, internet_plans
from app.schemas.responses.backend_response import BackendResponse
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
    "http://localhost:3000", # Frontend dev common port
    "http://localhost:8080", # Frontend dev common port
    "http://localhost:8081", # Chatbot interface dev server
    "http://localhost:8082", # Chatbot interface dev server (fallback)
    # "https://midominio.com" # Agregar dominios de producción aquí
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
    """
    return BackendResponse.success(action=None, data={"status": "ok", "service": "WispHub Local API"})

# Registrar manejadores de excepciones globales
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(clients.router)
app.include_router(tickets.router)
app.include_router(network.router)
app.include_router(internet_plans.router)