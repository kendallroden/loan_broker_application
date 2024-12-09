import json
import os

import requests
from dapr.clients import DaprClient

from fastapi import HTTPException
import grpc
import logging
from typing import List
from dapr.ext.workflow import DaprWorkflowContext, when_all

from model.bank_model import LoanRequestModel, Credit

logging.basicConfig(level=logging.INFO)

union_vault_appid = os.getenv('UNION_VAULT_APP_ID', '')
titanium_trust_appid = os.getenv('TITANIUM_TRUST_APP_ID', '')
riverstone_bank_appid = os.getenv('RIVERSTONE_APP_ID', '')

dapr_http_endpoint = os.getenv('DAPR_HTTP_ENDPOINT', 'http://localhost')
dapr_api_token = os.getenv('DAPR_API_TOKEN', '')
pubsub_component = os.getenv('PUBSUB_COMPONENT', 'pubsub')
subscription_topic = os.getenv('TOPIC_NAME', 'quotes')


def error_handler(ctx, error):
    logging.error(f'Executing error handler: {error}.')

    return "error"


def loan_broker_workflow(ctx: DaprWorkflowContext, wf_input: {}):
   
    
    logging.info(f'Loan broaker workflow started with instance id: {ctx.instance_id}')
    logging.info(f'Workflow input: {wf_input}')

    # schedule tasks to process the calls to each provider 
    try:
        loan_broker_results = [ctx.call_activity(riverstone_bank_quote, input=wf_input),
                          ctx.call_activity(titanium_trust_quote, input=wf_input),
                          ctx.call_activity(union_vault_quote, input=wf_input)]
        results = yield when_all(loan_broker_results)

        # aggregate the results and send them to another activity
        quote_aggregate = {
            'request_id': wf_input['request_id'],
            'results': results
        }

        yield ctx.call_activity(process_results, input=quote_aggregate)
    
    except Exception as e:
        yield ctx.call_activity(error_handler, input=str(e))
        raise


def riverstone_bank_quote(ctx, input: {}):
    credit = Credit(score=input['score'])
    loan_req = CreditLoanRequest(amount=input['amount'], term=input['term'], credit=credit)

    headers = {'dapr-app-id': riverstone_bank_appid, 'dapr-api-token': dapr_api_token,
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


def titanium_trust_quote(ctx, input: {}):
    credit = Credit(score=input['score'])
    loan_req = LoanRequestModel(amount=input['amount'], term=input['term'], credit=credit)
    headers = {'dapr-app-id': titanium_trust_appid, 'dapr-api-token': dapr_api_token,
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


def union_vault_quote(ctx, input: {}):
    credit = Credit(score=input['score'])
    loan_req = LoanRequestModel(amount=input['amount'], term=input['term'], credit=credit)
    headers = {'dapr-app-id': union_vault_appid, 'dapr-api-token': dapr_api_token,
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


def process_results(ctx, results: {}):
    with DaprClient() as d:
        logging.info('Processing results.%s', json.dumps(results))
        details = {
            "event_type": "quote-aggregate",
            "quote_aggregate": json.dumps(results)
        }

        # push aggregate results as an event to quote-aggregate
        d.publish_event(
            pubsub_name=dapr_pubsub,
            topic_name=dapr_subscription_topic,
            data=json.dumps(details),
            data_content_type='application/json',
        )

        return "success"
