import asyncio
import uvicorn
import io
import httpx
import os
import uuid
from io import BytesIO
from fastapi import FastAPI, UploadFile
from PIL import Image
from dispatcher import Dispatcher

dispatcher = Dispatcher()
app = FastAPI()

# READ FROM ENVIRONMENT VARIABLE INSTEAD OF HARDCODING
ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://127.0.0.1:8000')
ML_API_ENDPOINT = f"{ML_SERVICE_URL}/predict"

# NEW: Add request mapping for producer-consumer
pending_requests = {}  # Maps request_id -> asyncio.Future
workers_running = False

@app.on_event("startup")
async def startup_event():
    """Start background consumer workers"""
    global workers_running
    workers_running = True
    
    # Start 2 background workers that will call your get_inference function
    asyncio.create_task(consumer_worker(worker_id=1))
    asyncio.create_task(consumer_worker(worker_id=2))
    asyncio.create_task(consumer_worker(worker_id=3))
    asyncio.create_task(consumer_worker(worker_id=4))
    print("Started 4 consumer workers")

@app.on_event("shutdown") 
async def shutdown_event():
    """Stop workers"""
    global workers_running
    workers_running = False

async def consumer_worker(worker_id: int):
    """
    Background worker that continuously calls your get_inference function
    This is the CONSUMER part
    """
    print(f"Worker {worker_id} started")
    
    while workers_running:
        try:
            # Call your existing get_inference function
            result = await get_inference()
            print(f"Worker {worker_id} got result: {result}")
            
            # Find the oldest pending request and give it this result
            if pending_requests:
                # Get the first (oldest) pending request
                request_id = next(iter(pending_requests))
                future = pending_requests.pop(request_id)
                
                if not future.done():
                    future.set_result(result)
                    print(f"Worker {worker_id} delivered result to request {request_id[:8]}")
            
        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
            # If there's an error, still try to resolve a pending request
            if pending_requests:
                request_id = next(iter(pending_requests))
                future = pending_requests.pop(request_id)
                if not future.done():
                    future.set_exception(e)
        
        # Small delay to prevent busy loop
        await asyncio.sleep(0.1)
    
    print(f"Worker {worker_id} stopped")

@app.get("/")
async def home():
    return {'message': "hello"}

@app.post("/add_to_queue")
async def request_queue(image: UploadFile):
    """
    PRODUCER: This endpoint receives requests and waits for results
    Minimal changes to your original code
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Your original code (unchanged):
    await dispatcher.add_to_queue(image)
    queue_size = await dispatcher.qsize()  # this is not being used but a good stat.
    print("ml service url:{}".format(ML_SERVICE_URL))
    print("ml api endpoint:{}".format(ML_API_ENDPOINT))
    print(f"This is the qsize:{queue_size}")
    
    # NEW: Instead of calling get_inference() directly, wait for worker to process it
    future = asyncio.Future()
    pending_requests[request_id] = future
    
    try:
        # Wait for background worker to process your request
        predictions = await asyncio.wait_for(future, timeout=30.0)
        print(f"Request {request_id[:8]} got result: {predictions}")
        return {'prediction': predictions, 'queue_size': queue_size}
        
    except asyncio.TimeoutError:
        # Clean up on timeout
        pending_requests.pop(request_id, None)
        return {'error': 'Request timeout', 'queue_size': queue_size}

# Your original get_inference function (unchanged!)
async def get_inference():
    """
    CONSUMER: Your original function, now called by background workers
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
        response = await client.post(url=ML_API_ENDPOINT, files=files)
    
    print(response.json()['prediction'])
    return response.json()['prediction']
