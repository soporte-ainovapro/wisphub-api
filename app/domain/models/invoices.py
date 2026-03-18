from pydantic import BaseModel

class InvoiceResponse(BaseModel):
    id: int
    issue_date: str
    due_date: str
    payment_day: int
    status: str
    subtotal
    
    
    