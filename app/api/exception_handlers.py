from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.schemas.responses.backend_response import BackendResponse
from app.schemas.responses.response_actions import GeneralAction

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Captura los errores 422 de Pydantic (problemas de tipos o campos faltantes)
    y los envuelve en el estándar BackendResponse.
    """
    errors = exc.errors()
    simplified_errors = [f"{err['loc'][-1]}: {err['msg']}" for err in errors]
    error_msg = "; ".join(simplified_errors)
    
    response = BackendResponse.error(
        action=GeneralAction.ERROR,
        message=f"Error de validación: {error_msg}"
    )
    return JSONResponse(
        status_code=422,
        content=response.model_dump()
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Captura los errores HTTP (como 404 Not Found genéricos del framework)
    y los envuelve en el estándar BackendResponse.
    """
    response = BackendResponse.error(
        action=GeneralAction.ERROR,
        message=str(exc.detail)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Captura cualquier otro error interno (500) para asegurar que siempre
    se devuelva un JSON estructurado de BackendResponse.
    """
    response = BackendResponse.error(
        action=GeneralAction.ERROR,
        message="Ocurrió un error interno en el servidor."
    )
    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )
