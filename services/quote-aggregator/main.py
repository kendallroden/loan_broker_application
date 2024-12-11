import json
import time
import grpc
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import logging
import os
from dapr.clients import DaprClient
from dapr.clients.grpc._response import TopicEventResponse

statestore_component = os.getenv('QUOTE_AGGREGATE_TABLE', 'kvstore')

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_sub()
    yield
    shutdown_sub_stream()

app = FastAPI(lifespan=lifespan)

# Streaming subscription
def init_sub():
    with DaprClient() as d:
        
        logging.info('attempting to start subscription...')

        try:
            close_fn = d.subscribe_with_handler(
                    pubsub_name='pubsub', topic='quotes', handler_fn=loan_quotes, dead_letter_topic='undeliverable')
        
            app.state.close_fn_handler = close_fn

            logging.info('subscription started...')

        except grpc.RpcError as err:
                logging.info(f"Error={err}")
                raise HTTPException(status_code=500, detail=err.details())

def shutdown_sub_stream(): 
    logging.info('Closing subscription on shutdown...')
    app.state.close_fn_handler()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post('/loan-quotes')
def loan_quotes(event):
    with DaprClient() as d:
        try:
            
            logging.info(f"Received event from {event._source} which was published on {event._pubsub_name} topic {event._topic}")

            quote_aggregate = json.loads(event._data['quote_aggregate'])

            logging.info(f"Event contained aggregated quote with details: {quote_aggregate}")
            
            # save aggregate data
            d.save_state(store_name=statestore_component,
                         key=quote_aggregate["request_id"],
                         value=json.dumps(quote_aggregate),
                         state_metadata={"contentType": "application/json"})
            
            logging.info(f"Quote successfully saved to db {statestore_component}")

            return TopicEventResponse('success')

        except grpc.RpcError as err:
            logging.info(f"Error={err}")
            raise HTTPException(status_code=500, detail=err.details())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)