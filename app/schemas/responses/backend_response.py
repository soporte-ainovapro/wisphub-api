from typing import Generic, TypeVar, Any, Optional
from pydantic import BaseModel
from app.schemas.responses.response_actions import ResponseAction
from app.schemas.responses.response_types import ResponseType

T = TypeVar("T")

class BackendResponse(BaseModel, Generic[T]):
    ok: bool
    type: ResponseType
    action: ResponseAction
    data: Optional[T] = None
    message: Optional[str] = None
    meta: Optional[dict[str, Any]] = None

    @classmethod
    def success(cls, action: ResponseAction, data: Optional[T] = None, message: str = None, meta: dict = None):
        return cls(ok=True, type=ResponseType.success, action=action, data=data, message=message, meta=meta)

    @classmethod
    def error(cls, action: ResponseAction, message: str = None):
        return cls(ok=False, type=ResponseType.error, action=action, data=None, message=message)

    @classmethod
    def info(cls, action: ResponseAction, data: Optional[T] = None, message: str = None):
        return cls(ok=True, type=ResponseType.info, action=action, data=data, message=message)
