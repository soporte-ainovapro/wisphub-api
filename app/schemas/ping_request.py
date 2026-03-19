from pydantic import BaseModel


class PingRequest(BaseModel):
    pings: int
