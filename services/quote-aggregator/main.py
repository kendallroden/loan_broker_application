from dapr.clients import DaprClient
from fastapi import FastAPI, HTTPException
import logging
import os
from model.cloud_events import CloudEvent


pubsub_name = os.getenv('DAPR_PUB_SUB', '')
aggregate_quote_topic = os.getenv('DAPR_AGGREGATE_QUOTE_TOPIC_NAME', '')

app = FastAPI()

logging.basicConfig(level=logging.INFO)
@app.post('/subscribe/quote-aggregate')
def package_status_update(event: CloudEvent):
    with DaprClient() as d:

        logging.info(f'quote aggregate event: %s:' % event.model_dump_json())


