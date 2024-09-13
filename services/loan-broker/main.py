import json
import os

import requests
from dapr.clients import DaprClient
from fastapi import FastAPI, HTTPException
import grpc
import logging
from typing import List
from dapr.ext.workflow import WorkflowRuntime, DaprWorkflowClient, DaprWorkflowContext, when_all
from model.credit_bureau_model import CreditBureauModel
from model.workflow_input_model import WorkflowInputModel
from workflow import union_vault_quote, titanium_trust_quote, riverstone_bank_quote, process_results, \
    loan_broker_workflow, error_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_url = os.getenv('DAPR_HTTP_ENDPOINT', 'http://localhost')
target_credit_bureau_app_id = os.getenv('DAPR_CREDIT_BUREAU_APP_ID', '')
dapr_api_token = os.getenv('DAPR_API_TOKEN', '')
target_union_vault_app_id = os.getenv('DAPR_UNION_VAULT_APP_ID', '')
dapr_pub_sub = os.getenv('DAPR_PUB_SUB', '')
dapr_subscription_topic = os.getenv('DAPR_SUBSCRIPTION_TOPIC', '')
aggregate_table = os.getenv('DAPR_QUOTE_AGGREGATE_TABLE', '')
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



@app.post('/workflow/loan-request')
def request_loan_workflow(workflow_input:WorkflowInputModel):
    try:
        with DaprClient() as d:
            headers = {'dapr-app-id': target_credit_bureau_app_id, 'dapr-api-token': dapr_api_token,
                       'content-type': 'application/json'}
            # request/response
            logging.info(f'credit bureau request: {workflow_input.model_dump()}')

            credit_bureau = CreditBureauModel(request_id=workflow_input.request_id, SSN=workflow_input.SSN)
            result = requests.post(
                url='%s/credit-bureau' % base_url,
                json=credit_bureau.model_dump(),
                headers=headers
            )
            if result.ok:
                logging.info('Invocation successful with status code: %s' %
                             result.status_code)

                logging.info("result is %s" % result.json())

                credit_bureau = result.json()
                logging.info("credit score is {}".format(credit_bureau['body']['score']))

                # Start workflow

                start_workflow = d.start_workflow(
                    workflow_name='loan_broker_workflow',
                    input={
                        "request_id": workflow_input.request_id,
                        "amount": workflow_input.amount,
                        "term":workflow_input.term,
                        "score": credit_bureau['body']['score']
                    },
                    workflow_component="dapr"
                )
                logging.info(f'Starting workflow with instance id: {start_workflow.instance_id}')
                return {"message": "Workflow started successfully", "workflow_id": start_workflow.instance_id}



    except grpc.RpcError as err:
        logger.error(f"an error occured: {err}")
        raise HTTPException(status_code=500, detail=str(err))
