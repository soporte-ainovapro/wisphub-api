from enum import Enum
from pydantic import BaseModel

class ConnectionStatus(str, Enum):
    no_internet = "no_internet"
    stable = "stable"
    antenna_only = "antenna_only"
    error = "error"
    pending = "pending"

class PingResultResponse(BaseModel):
    status: ConnectionStatus
    message: str
