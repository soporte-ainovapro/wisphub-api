from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as v1_router
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.exception_handlers import validation_exception_handler, http_exception_handler, general_exception_handler

app = FastAPI(
    title="WispHub API",
    description="API de integración local con WispHub.",
    version="2.0.0"
)

# Configuración de CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["system"], response_model=dict)
async def health_check():
    """
    Ruta de comprobación del estado de salud (Health Check).
    Utilizado por balanceadores de carga y Docker para confirmar
    que el servidor está levantado y aceptando conexiones.
    (Public endpoint — no authentication required.)
    """
    return {"status": "ok", "service": "WispHub Local API"}

# Registrar manejadores de excepciones globales
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Protected: Business logic routers
app.include_router(v1_router)