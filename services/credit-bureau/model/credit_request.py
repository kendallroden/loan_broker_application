from pydantic import BaseModel


class CreditRequest(BaseModel):
    request_id: str
    SSN: str
