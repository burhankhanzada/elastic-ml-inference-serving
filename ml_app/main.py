import psutil
import logging
import asyncio
import time
import io
import threading

from prometheus_client import Counter, Gauge, Histogram
from prometheus_client.exposition import start_http_server

from fastapi import FastAPI, UploadFile, Request
from resnet_inference import ModelInference
from PIL import Image

# Object of ModelInference class
model_inference = ModelInference()
app = FastAPI()
start_http_server(9001)

# Define metrics
REQUEST_COUNT = Counter('ml_app_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
CPU_USAGE = Gauge('ml_app_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('ml_app_memory_usage_percent', 'Memory usage percentage')
RESPONSE_TIME = Histogram('ml_app_response_time_seconds', 'Request response time in seconds', ['endpoint'])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def update_system_metrics():
    while True:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            CPU_USAGE.set(cpu_percent)
            MEMORY_USAGE.set(memory_percent)
            logger.info(f"CPU: {cpu_percent}%, Memory: {memory_percent}%")
        except Exception as e:
            logger.error(f"Error in update_system_metrics: {e}")
        time.sleep(1)  # Synchronous sleep


@app.on_event('startup')
def startup():
    threading.Thread(target=update_system_metrics, daemon=True).start()
    logger.info("ML app metrics initiated")

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

# ML Inference Endpoints
@app.get("/")
async def home():
    return {'message': 'This is the ML-APP'}

@app.post("/predict")
async def predict(image: UploadFile):
    """
    This is a post request async function for model inferencing.
    """
    try:
        contents = await image.read()
        image = Image.open(io.BytesIO(contents))
        preprocessed_image = model_inference.transform_image(image)
        prediction = model_inference.predict(preprocessed_image)
        return {'prediction': prediction}
    except Exception as e:
        return {'Error': e}