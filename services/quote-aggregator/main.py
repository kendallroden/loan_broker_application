import json

import grpc
from fastapi import FastAPI, HTTPException
import logging
import os
from dapr.clients import DaprClient
from dapr.clients.grpc._response import TopicEventResponse
from model.cloud_events import CloudEvent

quote_aggregate_table = os.getenv('QUOTE_AGGREGATE_TABLE', '')

app = FastAPI()

logging.basicConfig(level=logging.INFO)

def main():
    with DaprClient() as client:
        close_fn = client.subscribe_with_handler(
                pubsub_name='pubsub', topic='quotes', handler_fn=loan_quotes, dead_letter_topic='undeliverable')
    while True: 
        time.sleep(1)
    
    print('Closing subscription...')

    close_fn()


def loan_quotes(event: CloudEvent) -> TopicEventResponse:
    with DaprClient() as d:
        try:

            logging.info(f'Received event: %s:' % {event.data["quote_aggregate"]})

            quote_aggregate = json.loads(event.data['quote_aggregate'])
            
            # save aggregate data
            d.save_state(store_name=quote_aggregate_table,
                         key=str(quote_aggregate['request_id']),
                         value=json.dumps(quote_aggregate),
                         state_metadata={"contentType": "application/json"})


        except grpc.RpcError as err:
            logging.info(f"Error={err}")
            raise HTTPException(status_code=500, detail=err.details())


if __name__ == '__main__':
    main()