import json
import os

import requests

from fastapi import  HTTPException
import grpc
import logging
from typing import List
from dapr.ext.workflow import  DaprWorkflowContext, when_all

from model.bank_model import LoanRequestModel, Credit

logging.basicConfig(level=logging.INFO)

dapr_http_endpoint = os.getenv('DAPR_HTTP_ENDPOINT', 'http://localhost')
dapr_api_token = os.getenv('DAPR_API_TOKEN', '')
target_credit_bureau_app_id = os.getenv('DAPR_CREDIT_BUREAU_APP_ID', '')
target_union_vault_app_id = os.getenv('DAPR_UNION_VAULT_APP_ID', '')
target_titanium_trust_app_id = os.getenv('DAPR_TITANIUM_TRUST_APP_ID', '')
target_riverstone_bank_app_id = os.getenv('DAPR_RIVERSTONE_APP_ID', '')


def error_handler(ctx, error):
    logging.error(f'Executing error handler: {error}.')

    return "error"


def loan_broker_workflow(ctx: DaprWorkflowContext, wf_input: int):
    # get a batch of N work items to process in parallel
    logging.info(f'Starting workflow with instance id: {ctx.instance_id}')
    # work_batch = yield ctx.call_activity(get_work_batch, input=wf_input)

    # schedule N parallel tasks to process the work items and wait for all to complete
    try:
        parallel_tasks = [ctx.call_activity(riverstone_bank_quote, input=1),
                          ctx.call_activity(titanium_trust_quote, input=1),
                          ctx.call_activity(union_vault_quote, input=1)]
        outputs = yield when_all(parallel_tasks)

        # aggregate the results and send them to another activity
        logging.info(f'Workflow outputs: {outputs}')

        #send aggregate to process results activity
        yield ctx.call_activity(process_results, input=outputs)
    except Exception as e:
        yield ctx.call_activity(error_handler, input=str(e))
        raise


def riverstone_bank_quote(ctx, work_item: int):
    credit = Credit(score=500)
    loan_req = LoanRequestModel(amount=4000, term=6, credit=credit)
    # assign package to available delivery guy.
    headers = {'dapr-app-id': target_riverstone_bank_app_id, 'dapr-api-token': dapr_api_token,
               'content-type': 'application/json'}
    # request/response
    try:
        result = requests.post(
            url='%s/loan/request' % dapr_http_endpoint,
            json=loan_req.model_dump(),

            headers=headers
        )

        if result.ok:
            logging.info('Invocation successful with status code: %s' %
                         result.json())
            logging.info("result from riverstone bank is %s" % result.json())

            return result.json()

        else:
            logging.error(
                'Error occurred while invoking App ID: %s' % result.reason)
            raise HTTPException(status_code=500, detail=result.reason)

    except grpc.RpcError as err:
        logging.error(f"ErrorCode={err.code()}")
        raise HTTPException(status_code=500, detail=err.details())


def titanium_trust_quote(ctx, work_item: int):
    credit = Credit(score=500)
    loan_req = LoanRequestModel(amount=4000, term=6, credit=credit)
    # assign package to available delivery guy.
    headers = {'dapr-app-id': target_titanium_trust_app_id, 'dapr-api-token': dapr_api_token,
               'content-type': 'application/json'}
    # request/response
    try:
        result = requests.post(
            url='%s/loan/request' % dapr_http_endpoint,
            json=loan_req.model_dump(),

            headers=headers
        )

        if result.ok:
            logging.info('Invocation successful with status code: %s' %
                         result.json())
            logging.info("result from titanium trust is %s" % result.json())

            return result.json()

        else:
            logging.error(
                'Error occurred while invoking App ID: %s' % result.reason)
            raise HTTPException(status_code=500, detail=result.reason)

    except grpc.RpcError as err:
        logging.error(f"ErrorCode={err.code()}")
        raise HTTPException(status_code=500, detail=err.details())


def union_vault_quote(ctx, work_item: int):
    credit = Credit(score=500)
    loan_req = LoanRequestModel(amount=4000, term=6, credit=credit)
    headers = {'dapr-app-id': target_union_vault_app_id, 'dapr-api-token': dapr_api_token,
               'content-type': 'application/json'}
    # request/response
    try:
        result = requests.post(
            url='%s/loan/request' % dapr_http_endpoint,
            json=loan_req.model_dump(),

            headers=headers
        )

        if result.ok:
            logging.info('Invocation successful with status code: %s' %
                         result.json())
            logging.info("result from union vault is %s" % result.json())

            return result.json()

        else:
            logging.error(
                'Error occurred while invoking App ID: %s' % result.reason)
            raise HTTPException(status_code=500, detail=result.reason)

    except grpc.RpcError as err:
        logging.error(f"ErrorCode={err.code()}")
        raise HTTPException(status_code=500, detail=err.details())


def process_results(ctx, results: List):
    logging.info('Processing results.%s', json.dumps(results))
    return "success"
