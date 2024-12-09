from pydantic import BaseModel


class LoanRequest(BaseModel):
    id: str
    SSN: str
    amount: int
    term: int
