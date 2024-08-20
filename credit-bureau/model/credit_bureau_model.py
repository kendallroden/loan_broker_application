from pydantic import BaseModel


class CreditBureauModel(BaseModel):
    request_id: str
    SSN: str
