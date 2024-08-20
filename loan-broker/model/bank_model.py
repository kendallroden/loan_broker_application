from pydantic import BaseModel


class Credit(BaseModel):
    score: int  # clients credit score


class LoanRequestModel(BaseModel):

    amount: int  # loan amount
    term: int  # the number of months until the loan has to be paid off
    credit: Credit
