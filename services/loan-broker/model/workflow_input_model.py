from pydantic import BaseModel


class WorkflowInputModel(BaseModel):
    request_id: str
    SSN: str
    amount: int
    term: int
