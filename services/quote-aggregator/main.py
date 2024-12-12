import json
import time
import grpc
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import logging
import os
from dapr.clients import DaprClient
from dapr.clients.grpc._response import TopicEventResponse
from model.cloud_events import CloudEvent

statestore_component = os.getenv('QUOTE_AGGREGATE_TABLE', 'kvstore')

logging.basicConfig(level=logging.INFO)

# region Declarative subscription
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post('/loan-quotes')
def loan_quotes(event: CloudEvent):
    with DaprClient() as d:
        try:

            logging.info(f"Event contained aggregated quote with details: {event.data}")

            quote_aggregate = json.loads(event.data["quote_aggregate"])

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
# endregion

# region Streaming subscription

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     init_sub()
#     yield
#     shutdown_sub_stream()

# app = FastAPI(lifespan=lifespan)

# @app.get("/")
# async def healthz():
#     return {"message": "Hello, World!"}

# # Streaming subscription
# def init_sub():
#     with DaprClient() as d:
        
#         logging.info('Attempting to start subscription...')

#         try:
#             close_fn = d.subscribe_with_handler(
#                     pubsub_name='pubsub', topic='quotes', handler_fn=loan_quotes, dead_letter_topic='undeliverable')
        
#             app.state.close_fn_handler = close_fn

#             logging.info('Subscription started...')

#         except grpc.RpcError as err:
#                 logging.info(f"Error={err}")
#                 raise HTTPException(status_code=500, detail=err.details())

#         while True:
#             time.sleep(1)

# def shutdown_sub_stream(): 
#     logging.info('Closing subscription...')
#     app.state.close_fn_handler()

# def loan_quotes(event):
#     logging.info(f"Received event from {event.source()} which was published on {event.pubsub_name()} topic {event.topic()}: {event.data()}")

#     with DaprClient() as d:
#         try:
#             # logging.info(f"Received event from {event._source} which was published on {event._pubsub_name} topic {event._topic}: {event._data}")

#             # ignore malformed events
#             if event.data() is None:
#                 logging.info(f"Event data is None, ignoring...")
#                 return TopicEventResponse('success')

#             quote_aggregate = event.data()
#             if not "request_id" in quote_aggregate:
#                 logging.info(f"Event data does not contain request_id, ignoring...")
#                 return TopicEventResponse('success')

#             logging.info(f"Event contained aggregated quote with details: {quote_aggregate}")
            
#             # save aggregate data
#             d.save_state(store_name=statestore_component,
#                          key=quote_aggregate["request_id"],
#                          value=json.dumps(quote_aggregate),
#                          state_metadata={"contentType": "application/json"})
            
#             logging.info(f"Quote successfully saved to db {statestore_component}")

#             return TopicEventResponse('success')

#         except grpc.RpcError as err:
#             logging.info(f"Error={err}")
#             raise HTTPException(status_code=500, detail=err.details())
# endregion

if __name__ == "__main__":
    uvicorn.run(app, port=5002)
