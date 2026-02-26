from enum import Enum
from typing import Union

class ClientAction(str, Enum):
    FOUND = "client_found"
    NOT_FOUND = "client_not_found"
    INVALID_DOCUMENT = "invalid_document"
    LISTED = "clients_listed"
    UPDATED = "client_updated"
    UPDATE_FAILED = "client_update_failed"
    VERIFIED = "client_verified"
    VERIFICATION_FAILED = "client_verification_failed"

class TicketAction(str, Enum):
    CREATED = "ticket_created"
    CREATION_FAILED = "ticket_creation_failed"
    NOT_FOUND = "ticket_not_found"
    FOUND = "ticket_found"
    ZONE_LIMIT_REACHED = "zone_ticket_limit_reached"

class NetworkAction(str, Enum):
    PING_SUCCESS = "ping_success"
    PING_FAILED = "ping_failed"
    PING_CREATED = "ping_created"
    NO_INTERNET = "no_internet"
    INTERMITTENT = "intermittent_connection"
    STABLE = "stable_connection"

class PlanAction(str, Enum):
    LISTED = "internet_plans_listed"
    NOT_FOUND = "internet_plan_not_found"
    FOUND = "internet_plan_found"

class GeneralAction(str, Enum):
    REDIRECT_SALES = "redirect_sales"
    SHOW_PAYMENT_INFO = "show_payment_info"
    ERROR = "error"

# Export a Union Type of all possible Domain Actions for Pydantic Validation
ResponseAction = Union[ClientAction, TicketAction, NetworkAction, PlanAction, GeneralAction]
