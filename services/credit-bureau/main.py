import random
import re
from fastapi import FastAPI, HTTPException
import grpc
import logging
from model.credit_request import CreditRequest

logging.basicConfig(level=logging.INFO)

def get_random_int(min_value, max_value):
    return min_value + random.randint(0, max_value - min_value)


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post('/credit-score')
def credit_bureau_service(cbModel: CreditRequest):
    
    min_score = 300
    max_score = 900

    ssn_regex = re.compile(r"^\d{3}-\d{2}-\d{4}$")
    if ssn_regex.match(cbModel.SSN):
        return {
            'statusCode': 200,
            'request_id': cbModel.request_id,
            'body': {
                'SSN': cbModel.SSN,
                'score': get_random_int(min_score, max_score),
                'history': get_random_int(1, 30),
            }
        }
    else:
        return {
            'statusCode': 400,
            'request_id': cbModel.request_id,
            'body': {
                'SSN': cbModel.SSN,
            }
        }
