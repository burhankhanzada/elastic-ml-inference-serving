import asyncio
import httpx
import logging
from kubernetes import client, config
import time
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROMETHEUS_URL = "http://prometheus-operated.monitoring.svc:9090"
DEPLOYMENT_NAME = "ml-app-deployment"
NAMESPACE = "default"
POLL_INTERVAL = 15  # Seconds
COOLDOWN_SECONDS = 300  # 5 minutes
MIN_REPLICAS = 1
MAX_REPLICAS = 4
DESIRED_METRICS = {
    "qsize": 10,  # Desired dispatcher_queue_size per replica
    "disp_cpu": 10,  # Desired dispatcher CPU usage % per replica
    "disp_mem": 50,  # Desired dispatcher memory usage % per replica
    "ml_cpu": 30,  # Desired ml-app CPU usage % per replica
    "ml_mem": 30,  # Desired ml-app memory usage % per replica
}

async def get_metric(query):
    """Get a single metric value from Prometheus."""
    prometheus_url = f"{PROMETHEUS_URL}/api/v1/query"
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
        logger.error(f"Connection error for {query}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error for {query}: Status {e.response.status_code}, {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {query}: {e}")
        return None

async def scale_deployment(disp_qsize, disp_cpu, disp_mem, ml_cpu, ml_mem):
    """Scale ml-app-deployment based on metrics."""
    logger.info("Attempting to scale deployment")
    global last_scale_time
    if time.time() - last_scale_time < COOLDOWN_SECONDS:
        logger.info(f"Skipping scale due to cooldown (last scaled {time.time() - last_scale_time:.1f}s ago)")
        return

    # Get current replicas
    try:
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        current_replicas = deployment.spec.replicas
        logger.info(f"Current replicas: {current_replicas}")
    except client.exceptions.ApiException as e:
        logger.error(f"Failed to get current replicas: {e}")
        current_replicas = 1  # Fallback

    # Fallback metrics for ml-app
    if ml_cpu is None:
        ml_cpu_query = 'sum(rate(container_cpu_usage_seconds_total{namespace="default",container="ml-app"}[1m])) * 100'
        ml_cpu = await get_metric(ml_cpu_query)
        logger.info(f"Fallback ml_cpu: {ml_cpu}%")
    if ml_mem is None:
        ml_mem_query = 'sum(container_memory_usage_bytes{namespace="default",container="ml-app"}) / (1024 * 1024 * 1024) / 4 * 100'
        ml_mem = await get_metric(ml_mem_query)
        logger.info(f"Fallback ml_mem: {ml_mem}%")

    # Calculate desired replicas using ceil[currentReplicas * (currentMetricValue / desiredMetricValue)]
    replicas_list = []
    metrics = {
        "qsize": disp_qsize,
        "disp_cpu": disp_cpu,
        "disp_mem": disp_mem,
        "ml_cpu": ml_cpu,
        "ml_mem": ml_mem
    }
    for metric_name, current_value in metrics.items():
        if current_value is not None and current_value > 0:  # Avoid division by zero or None
            desired_value = DESIRED_METRICS[metric_name]
            desired_replicas = math.ceil(current_replicas * (current_value / desired_value))
            replicas_list.append(desired_replicas)
            logger.info(f"Metric {metric_name}: {current_value}, Desired: {desired_value}, Replicas: {desired_replicas}")
        else:
            logger.warning(f"Metric {metric_name} is None or 0, skipping replica calculation")

    # Take max replicas, constrain between MIN_REPLICAS and MAX_REPLICAS
    desired_replicas = max(replicas_list) if replicas_list else current_replicas
    desired_replicas = max(MIN_REPLICAS, min(MAX_REPLICAS, desired_replicas))
    logger.info(f"Desired replicas: {desired_replicas} (Metrics: Qsize={disp_qsize}, Disp_CPU={disp_cpu}%, Disp_Mem={disp_mem}%, ML_CPU={ml_cpu}%, ML_Mem={ml_mem}%)")

    # Apply scaling
    if desired_replicas != current_replicas:
        try:
            apps_v1.patch_namespaced_deployment_scale(
                name=DEPLOYMENT_NAME,
                namespace=NAMESPACE,
                body={"spec": {"replicas": desired_replicas}}
            )
            logger.info(f"Scaled {DEPLOYMENT_NAME} from {current_replicas} to {desired_replicas} replicas")
            last_scale_time = time.time()
        except client.exceptions.ApiException as e:
            logger.error(f"Error scaling deployment: {e}")
    else:
        logger.info("No scaling action taken")

async def main():
    """Run autoscaler every 15 seconds."""
    logger.info("Starting scale cycle")
    disp_qsize = await get_metric('dispatcher_queue_size{job="dispatcher-service", namespace="default"}')
    disp_cpu = await get_metric('dispatcher_cpu_usage_percent{job="dispatcher-service", namespace="default"}')
    disp_mem = await get_metric('dispatcher_memory_usage_percent{job="dispatcher-service", namespace="default"}')
    ml_cpu = await get_metric('ml_app_cpu_usage_percent{job="ml-app-service", namespace="default"}')
    ml_mem = await get_metric('ml_app_memory_usage_percent{job="ml-app-service", namespace="default"}')
    logger.info(f"Queue Size: {disp_qsize}, Disp_CPU: {disp_cpu}, Disp_Mem: {disp_mem}, ML_CPU: {ml_cpu}, ML_Mem: {ml_mem}")
    await scale_deployment(disp_qsize, disp_cpu, disp_mem, ml_cpu, ml_mem)

if __name__ == "__main__":
    logger.info("Entering infinite loop")
    try:
        config.load_incluster_config()
    except config.ConfigException:
        logger.error("Failed to load in-cluster config, falling back to kubeconfig")
        config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    last_scale_time = 0
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            loop.run_until_complete(main())
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        logger.info(f"Sleeping for 15 seconds at {loop.time()}")
        loop.run_until_complete(asyncio.sleep(15))