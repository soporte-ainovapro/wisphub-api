from enum import Enum


class ConnectionStatus(str, Enum):
    no_internet = "no_internet"
    stable = "stable"
    error = "error"
    pending = "pending"
