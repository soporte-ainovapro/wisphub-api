from enum import Enum

class ConnectionStatus (str, Enum):
    no_internet = "no_internet"
    intermittent = "intermittent"
    stable = "stable"
    
    error = "error"
    pending= "pending"