import json
import os

import requests
from dapr.clients import DaprClient
from fastapi import FastAPI, HTTPException
import grpc
import logging
from typing import List
from dapr.ext.workflow import WorkflowRuntime, DaprWorkflowClient, DaprWorkflowContext, when_all
from model.credit_bureau_model import CreditRequest
from model.loan_request import LoanRequest
from workflow import union_vault_quote, titanium_trust_quote, riverstone_bank_quote, process_results, loan_broker_workflow, error_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

credit_bureau_appid = os.getenv('DAPR_CREDIT_BUREAU_APP_ID', '')
dapr_api_token = os.getenv('DAPR_API_TOKEN', '')
dapr_http_endpoint = os.getenv('DAPR_HTTP_ENDPOINT', 'http://localhost')

app = FastAPI()

workflow_runtime = WorkflowRuntime()
workflow_runtime.register_workflow(loan_broker_workflow)
workflow_runtime.register_activity(union_vault_quote)
workflow_runtime.register_activity(titanium_trust_quote)
workflow_runtime.register_activity(riverstone_bank_quote)
workflow_runtime.register_activity(process_results)
workflow_runtime.register_activity(error_handler)
workflow_runtime.start()


@app.post('/loan-request')
def request_loan_workflow(loan_request:LoanRequest):
    try:
        with DaprClient() as d:
            headers = {'dapr-app-id': credit_bureau_app_id, 'dapr-api-token': dapr_api_token, 'content-type': 'application/json'}
            
            # Send request to retrieve credit score
            logging.info(f'credit bureau request: {loan_request.model_dump()}')

            credit_bureau = CreditBureauModel(request_id=loan_request.id, SSN=loan_request.SSN)
            
            result = requests.post(
                url='%s/credit-score' % dapr_http_endpoint,
                json=credit_bureau.model_dump(),
                headers=headers
            )
            if result.ok:
                
                logging.info('Credit score retrieved from credit bureau with status code: %s' % result.status_code)

                credit_score = result.json()
                logging.info("Credit score is {}".format(credit_score['body']['score']))

                # Start workflow

                start_workflow = d.start_workflow(
                    workflow_name='loan_broker_workflow',
                    input={
                        "request_id": loan_request.id,
                        "amount": loan_request.amount,
                        "term":loan_request.term,
                        "score": credit_score['body']['score']
                    },
                    workflow_component="dapr"
                )
                
                return {"message": "Loan broker workflow started", "workflow_id": start_workflow.instance_id}


    except grpc.RpcError as err:
        logger.error(f"An error occured: {err}")
        raise HTTPException(status_code=500, detail=str(err))
