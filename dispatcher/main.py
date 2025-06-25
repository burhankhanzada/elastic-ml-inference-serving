import asyncio
import aiohttp
import os
import uuid
import time
import httpx
import psutil
import logging

from aiohttp import ClientSession, TCPConnector
from prometheus_client import Counter, Gauge, Histogram
from prometheus_client.exposition import start_http_server
from io import BytesIO
from fastapi import FastAPI, UploadFile, Request
from PIL import Image
from dispatcher import Dispatcher


dispatcher = Dispatcher()
app = FastAPI()

# Define metrics
REQUEST_COUNT = Counter('dispatcher_requests', 'Total HTTP requests', ['method', 'endpoint', 'status'])
QUEUE_SIZE = Gauge('dispatcher_queue_size', 'Number of tasks in the ML inference queue')
CPU_USAGE = Gauge('dispatcher_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('dispatcher_memory_usage_percent', 'Memory usage percentage')
RESPONSE_TIME = Histogram('dispatcher_response_time_seconds', 'Request response time in seconds', ['endpoint'])


# READ FROM ENVIRONMENT VARIABLE INSTEAD OF HARDCODING
ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://127.0.0.1:8000')
ML_API_ENDPOINT = f"{ML_SERVICE_URL}/predict"

# Shared HTTP client for connection pooling
HTTP_CLIENT = None

# Start Prometheus metrics server
start_http_server(9000)  # Exposes metrics at http://localhost:9000

# NEW: Add request mapping for producer-consumer
pending_requests = {}  # Maps request_id -> asyncio.Future
pending_requests_lock = asyncio.Lock()  # Prevent race conditions
workers_running = False

@app.on_event("startup")
async def startup_event():
    """Start background consumer workers"""
    global workers_running, HTTP_CLIENT
    workers_running = True
    
    # Create shared HTTP client with timeout and connection pooling
    HTTP_CLIENT = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=0)
    )
    
    # Start 2 background workers that will call your get_inference function
    asyncio.create_task(consumer_worker(worker_id=1))
    asyncio.create_task(consumer_worker(worker_id=2))
    asyncio.create_task(consumer_worker(worker_id=3))
    asyncio.create_task(consumer_worker(worker_id=4))
    asyncio.create_task(consumer_worker(worker_id=5))
    asyncio.create_task(consumer_worker(worker_id=6))
    asyncio.create_task(consumer_worker(worker_id=7))
    asyncio.create_task(consumer_worker(worker_id=8))
    asyncio.create_task(consumer_worker(worker_id=9))
    asyncio.create_task(consumer_worker(worker_id=10))    
    asyncio.create_task(update_system_metrics())
    print("Started 10 consumer workers and system metrics")

@app.on_event("shutdown") 
async def shutdown_event():
    """Stop workers"""
    global workers_running, HTTP_CLIENT
    workers_running = False
    if HTTP_CLIENT:
        await HTTP_CLIENT.aclose()

# Background task to update system metrics
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_system_metrics():
    while True:
        try:
            cpu_percent = psutil.cpu_percent(interval=.1)
            memory_percent = psutil.virtual_memory().percent
            queue_size = await dispatcher.qsize()
            CPU_USAGE.set(cpu_percent)
            MEMORY_USAGE.set(memory_percent)
            QUEUE_SIZE.set(queue_size)
            logger.info(f"CPU: {cpu_percent}%, Memory: {memory_percent}%, Queue: {queue_size}")
        except Exception as e:
            logger.error(f"Error in update_system_metrics: {e}")
        await asyncio.sleep(1)
# Middleware to track response time and request count
@app.middleware('http')
async def add_metrics(request: Request, call_next):
    method = request.method
    endpoint = request.url.path
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    status = response.status_code
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    RESPONSE_TIME.labels(endpoint=endpoint).observe(time.time() - start_time)
    
    return response
#================================DISPATCHER===============================================
async def consumer_worker(worker_id: int):
    """
    Background worker that continuously calls your get_inference function
    This is the CONSUMER part
    """
    print(f"Worker {worker_id} started")
    
    while workers_running:
        try:
            # Call your existing get_inference function
            result, request_id = await get_inference()  # Now returns (result, request_id)
            print(f"Worker {worker_id} got result: {result}")
            
            # Find the correct pending request and give it this result (thread-safe)
            async with pending_requests_lock:
                future = pending_requests.pop(request_id, None)
                
                if future and not future.done():
                    future.set_result(result)
                    print(f"Worker {worker_id} delivered result to request {request_id[:8]}")
            
        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
            # If there's an error, still try to resolve a pending request
            async with pending_requests_lock:
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
    return {'message': "This is the DISPATCHER APP"}

@app.post("/add_to_queue")
async def request_queue(image: UploadFile):
    """
    PRODUCER: This endpoint receives requests and waits for results
    Minimal changes to your original code
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Your original code (minimal change):
    await dispatcher.add_to_queue(image, request_id)  # Pass request_id for correlation
    queue_size = await dispatcher.qsize()  # this is not being used but a good stat.
    print("ml service url:{}".format(ML_SERVICE_URL))
    print("ml api endpoint:{}".format(ML_API_ENDPOINT))
    print(f"This is the qsize:{queue_size}")
    # return {'queue_size': queue_size}
    # NEW: Instead of calling get_inference() directly, wait for worker to process it
    future = asyncio.Future()
    async with pending_requests_lock:  # Thread-safe access
        pending_requests[request_id] = future
    
    try:
        # Wait for background worker to process your request
        predictions = await asyncio.wait_for(future, timeout=60)  # Increased from 5 to 70
        print(f"Request {request_id[:8]} got result: {predictions}")
        return {'prediction': predictions, 'queue_size': queue_size}
        
    except asyncio.TimeoutError:
        # Clean up on timeout
        async with pending_requests_lock:  # Thread-safe cleanup
            pending_requests.pop(request_id, None)
        return {'error': 'Request timeout', 'queue_size': queue_size}

async def get_inference():
    """
    CONSUMER: Your original function, now called by background workers
    - get request item from queue
    - post request item to the /predict endpoint  
    - get result = {prediction:class + confidence}
    """
    request_queue = dispatcher.request_queue
    queue_item, request_id = await request_queue.get()  # Now get tuple (image, request_id)
    # print(queue_item)
    
    # Convert PIL to bytes
    img_buffer = BytesIO()
    queue_item.save(img_buffer, format='JPEG')
    files = {"image": ("image.jpg", img_buffer.getvalue(), "image/jpeg")}
    img_buffer.close()
    
    # Use shared HTTP client with timeout
    response = await HTTP_CLIENT.post(url=ML_API_ENDPOINT, files=files)
    
    print(response.json()['prediction'])
    return response.json()['prediction'], request_id  # Return both result and request_id