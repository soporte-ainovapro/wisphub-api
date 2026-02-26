from enum import Enum

class ResponseType(str, Enum):
    success= "success"
    error= "error"
    info= "info"