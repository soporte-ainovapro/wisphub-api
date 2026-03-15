from enum import Enum

class ClientAction(str, Enum):
    FOUND = "client_found"
    NOT_FOUND = "client_not_found"
    INVALID_DOCUMENT = "invalid_document"
    LISTED = "clients_listed"
    UPDATED = "client_updated"
    UPDATE_FAILED = "client_update_failed"
    VERIFIED = "client_verified"
    VERIFICATION_FAILED = "client_verification_failed"
