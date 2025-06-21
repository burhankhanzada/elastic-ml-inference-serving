import asyncio
import httpx
import logging
from kubernetes import client, config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def get_metric(query):
    """Get a single metric value from Prometheus."""
    prometheus_url = "http://prometheus-operated.monitoring.svc:9090/api/v1/query"
    logger.info(f"Attempting to fetch metric: {query} at {prometheus_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(prometheus_url, params={"query": query}, timeout=5)
            response.raise_for_status()
            result = response.json()
            
            if result["status"] == "success" and result["data"]["result"]:
                value = float(result["data"]["result"][0]["value"][1])
                logger.info(f"Metric {query}: {value}")
                return value
            
            logger.warning(f"No data for query: {query}, result: {result}")
            return None
            
    except httpx.ConnectError as e:
        logger.error(f"Connection error for {query} at {prometheus_url}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error for {query} at {prometheus_url}: Status {e.response.status_code}, {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {query} at {prometheus_url}: {e}")
        return None

async def scale_deployment(qsize, cpu, memory):
    """Scale ml-app-deployment based on metrics."""
    logger.info("Attempting to scale deployment")
    
    config.load_incluster_config()
    apps_v1 = client.AppsV1Api()
    name = "ml-app-deployment"
    namespace = "default"
    
    # Get current replicas
    try:
        deployment = apps_v1.read_namespaced_deployment(name, namespace)
        current_replicas = deployment.spec.replicas
        logger.info(f"Current replicas: {current_replicas}")
    except Exception as e:
        logger.error(f"Failed to get current replicas: {e}")
        current_replicas = 1  # fallback
    
    # Calculate desired replicas based on all metrics
    desired_replicas = current_replicas
    
    # Scale up conditions
    if (qsize and qsize > 50) or (cpu and cpu > 70) or (memory and memory > 80):
        desired_replicas = min(current_replicas + 1, 4)  # max 4 replicas
        logger.info(f"Scale UP triggered - Queue: {qsize}, CPU: {cpu}%, Memory: {memory}%")
    
    # Scale down conditions
    elif (qsize is not None and qsize < 10) and (cpu is not None and cpu < 30) and (memory is not None and memory < 40):
        desired_replicas = max(current_replicas - 1, 1)  # min 1 replica
        logger.info(f"Scale DOWN triggered - Queue: {qsize}, CPU: {cpu}%, Memory: {memory}%")
    
    else:
        logger.info(f"No scaling needed - Queue: {qsize}, CPU: {cpu}%, Memory: {memory}%")
    
    # Apply scaling if needed
    if desired_replicas != current_replicas:
        body = {"spec": {"replicas": desired_replicas}}
        try:
            apps_v1.patch_namespaced_deployment_scale(name, namespace, body)
            logger.info(f"Scaled {name} from {current_replicas} to {desired_replicas} replicas")
        except client.rest.ApiException as e:
            logger.error(f"Failed to scale {name}: {e}")
    else:
        logger.info("No scaling action taken")

async def main():
    logger.info("Starting main loop")
    
    qsize = await get_metric('dispatcher_queue_size{job="dispatcher-service", namespace="default"}')
    cpu = await get_metric('ml_app_cpu_usage_percent{job="ml-app-service", namespace="default"}')
    memory = await get_metric('ml_app_memory_usage_percent{job="ml-app-service", namespace="default"}')
    
    logger.info(f"Queue Size: {qsize}, CPU: {cpu}, Memory: {memory}")
    
    await scale_deployment(qsize, cpu, memory)

if __name__ == "__main__":
    logger.info("Entering infinite loop")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        try:
            loop.run_until_complete(main())
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        
        logger.info(f"Sleeping for 15 seconds at {loop.time()}")
        loop.run_until_complete(asyncio.sleep(15))  # Run every minute