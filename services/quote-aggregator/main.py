import json

import grpc
from dapr.clients import DaprClient
from fastapi import FastAPI, HTTPException
import logging
import os
from model.cloud_events import CloudEvent

quote_aggregate_table = os.getenv('DAPR_QUOTE_AGGREGATE_TABLE', '')

app = FastAPI()

logging.basicConfig(level=logging.INFO)


@app.post('/bureau/quote-aggregate')
def quote_aggregate(event: CloudEvent):
    with DaprClient() as d:
        try:

            logging.info(f'quote aggregate event: %s:' % event.model_dump_json())
            logging.info(f'Received event: %s:' % {event.data['quote-aggregate']})

            quote_aggregate = json.loads(event.data['quote-aggregate'])
            # save aggregate data
            d.save_state(store_name=quote_aggregate_table,
                         key=str(quote_aggregate['request_id']),
                         value=json.dumps(quote_aggregate),
                         state_metadata={"contentType": "application/json"})

            logging.info("Group Info saved successfully")
        except grpc.RpcError as err:
            logging.info(f"Error={err}")
            raise HTTPException(status_code=500, detail=err.details())
