import os

import requests
from dapr.clients import DaprClient
from fastapi import FastAPI, HTTPException
import grpc
import logging
from typing import List
from dapr.ext.workflow import WorkflowRuntime, DaprWorkflowClient, DaprWorkflowContext, when_all
from model.credit_bureau_model import CreditBureauModel
from model.bank_model import LoanRequestModel, Credit
from workflow import union_vault_quote,titanium_trust_quote,riverstone_bank_quote,process_results,loan_broker_workflow,error_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_url = os.getenv('DAPR_HTTP_ENDPOINT', 'http://localhost')
target_credit_bureau_app_id = os.getenv('DAPR_CREDIT_BUREAU_APP_ID', '')
dapr_api_token = os.getenv('DAPR_API_TOKEN', '')
target_union_vault_app_id = os.getenv('DAPR_UNION_VAULT_APP_ID', '')

target_titanium_trust_app_id = os.getenv('DAPR_TITANIUM_TRUST_APP_ID', '')

target_riverstone_bank_app_id = os.getenv('DAPR_RIVERSTONE_BANK_APP_ID', '')

app = FastAPI()

workflow_runtime = WorkflowRuntime()
workflow_runtime.register_workflow(loan_broker_workflow)
workflow_runtime.register_activity(union_vault_quote)
workflow_runtime.register_activity(titanium_trust_quote)
workflow_runtime.register_activity(riverstone_bank_quote)
workflow_runtime.register_activity(process_results)
workflow_runtime.register_activity(error_handler)
workflow_runtime.start()


@app.post('/request/credit-bureau')
def request_credit_score(credit_bureau: CreditBureauModel):
    # assign package to available delivery guy.
    headers = {'dapr-app-id': target_credit_bureau_app_id, 'dapr-api-token': dapr_api_token,
               'content-type': 'application/json'}
    # request/response
    logging.info(f'credit bureau request: {credit_bureau.model_dump()}')
    try:
        result = requests.post(
            url='%s/v1.0/credit-bureau' % base_url,
            json=credit_bureau.model_dump(),
            headers=headers
        )

        if result.ok:
            logging.info('Invocation successful with status code: %s' %
                         result.status_code)
            logging.info("result is %s" % result.json())
            #credit_bureau = result.json()

            return result.json()

        else:
            logging.error(
                'Error occurred while invoking App ID: %s' % result.reason)
            raise HTTPException(status_code=500, detail=result.reason)

    except grpc.RpcError as err:
        logging.error(f"ErrorCode={err.code()}")
        raise HTTPException(status_code=500, detail=err.details())


@app.post('/workflow/loan-request')
def request_loan_workflow():
    try:
        with DaprClient() as d:
            start_workflow = d.start_workflow(
                workflow_name='loan_broker_workflow',
                input=3,
                workflow_component="dapr"
            )
            logging.info(f'Starting workflow with instance id: {start_workflow.instance_id}')
            return {"message": "Workflow started successfully", "workflow_id": start_workflow.instance_id}

    except grpc.RpcError as err:
        logger.error(f"Failed to start workflow: {err}")
        raise HTTPException(status_code=500, detail=str(err))









