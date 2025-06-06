import asyncio
import uvicorn
import io
import httpx

from io import BytesIO
from fastapi import FastAPI, UploadFile
from PIL import Image
from dispatcher import Dispatcher

dispatcher = Dispatcher()
app = FastAPI()

ML_API_ENDPOINT = "http://127.0.0.1:8000/predict"

@app.get("/")
async def home():
    return {'message': "hello"}

@app.post("/add_to_queue")
async def request_queue(image:UploadFile):
    """
    This endpoint receives the requests from the load_tester and stores them in a queue.
    """
    await dispatcher.add_to_queue(image)
    queue_size = await dispatcher.qsize() # this is not being used but a good stat.
    
    print(queue_size)
    # print(queue_size)
    
    # predictions = await get_inference()#
    # # print(prediction_task)
    
    # # return {'status': 'queued', 'queue_size': queue_size}
    # return {'prediction': predictions} # this is just for testing. 

@app.get("/get_predictions")
async def get_inference():
    """
    - get request item from queue
    - post request item to the /predict endpoint
    - get result = {prediction:class + confidence}
    """
    request_queue = dispatcher.request_queue
    queue_item = await request_queue.get()
    # print(queue_item)
    
    # Convert PIL to bytes
    img_buffer = BytesIO()
    queue_item.save(img_buffer, format='JPEG')
    files = {"image": ("image.jpg", img_buffer.getvalue(), "image/jpeg")}
    img_buffer.close()

    # httpx format
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url= ML_API_ENDPOINT, files=files)
        print(response.json()['prediction'])
        return response.json()['prediction']

