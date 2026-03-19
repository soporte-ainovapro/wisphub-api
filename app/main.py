import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api.v1 import router as v1_router
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.exception_handlers import validation_exception_handler, http_exception_handler, general_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-calienta la caché de clientes en background al arrancar."""
    async def _warm_up():
        try:
            from app.api.deps import get_client_service
            await get_client_service().get_all()
        except Exception:
            pass  # best-effort: no bloquea ni falla el arranque

    asyncio.create_task(_warm_up())
    yield


app = FastAPI(
    lifespan=lifespan,
    title="WispHub API",
    description="API de integración local con WispHub.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url=None,
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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schema["components"]["securitySchemes"] = {
        "ApiKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        }
    }

    for path in schema.get("paths", {}).values():
        for operation in path.values():
            operation["security"] = [{"ApiKeyHeader": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi