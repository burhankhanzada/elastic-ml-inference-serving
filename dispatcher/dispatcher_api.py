import asyncio
import uvicorn
import io

from fastapi import FastAPI, UploadFile
from PIL import Image
from dispatcher import Dispatcher

dispatcher = Dispatcher()
app = FastAPI()


@app.post("/request_queue")
async def request_queue(image:UploadFile):
    """
    This endpoint receives the requests from the load_tester and stores them in a queue.
    """
    _, request_queue = await dispatcher.store_requests(image)
    queue_size = await dispatcher.qsize(request_queue) 
    print(f"Inside View of queue:{_}\nQueue Size:{queue_size}")
    
    return {'prediction': queue_size} # this is just for testing. 

    # image_bytes = await image.read() # Seems like I got the image filename stored in the variable.
    # image = Image.open(io.BytesIO(image_bytes))
    # dispatcher.request = image
    # print(dispatcher.request)
    # await dispatcher.request_queue.put(dispatcher.request)
    # # stores the queue size in the queue size attribute in the dispatcher class
    # await dispatcher.qsize(dispatcher.request_queue)
    # print(dispatcher.queue_size)
    # # print(dispatcher.request_queue._queue)
    # # return {dispatcher.request: dispatcher.queue_size}


# @app.post("/")
# async def get_inference(queue:dispatcher.request_queue):
#     """
#     for request in queue:
#         - post request to the /predict endpoint
#         - get result = {prediction:class + confidence}
#     """
    
#     pass
