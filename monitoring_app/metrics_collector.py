import asyncio
import httpx
import psutil
import time
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    name: str
    url: str
    health_endpoint: str = "/health"
    metrics_endpoint: str = "/metrics"
    timeout: float = 5.0

class MetricsCollector:
    def __init__(self, services: List[ServiceConfig]):
        self.services = services
        self.client = httpx.AsyncClient(timeout=10.0)
        
        # Prometheus metrics for monitoring the monitored services
        self.service_up = Gauge(
            'monitored_service_up',
            'Whether a service is up (1) or down (0)',
            ['service_name', 'service_url']
        )
        
        self.service_response_time = Histogram(
            'monitored_service_response_time_seconds',
            'Response time of monitored services',
            ['service_name', 'endpoint']
        )
        
        self.service_request_rate = Gauge(
            'monitored_service_request_rate',
            'Request rate of monitored services (requests/sec)',
            ['service_name']
        )
        
        self.service_error_rate = Gauge(
            'monitored_service_error_rate',
            'Error rate of monitored services',
            ['service_name']
        )
        
        self.queue_size = Gauge(
            'monitored_queue_size',
            'Queue size from dispatcher service'
        )
        
        self.prediction_count = Counter(
            'monitored_predictions_total',
            'Total predictions made by ML service'
        )
        
        self.system_cpu_usage = Gauge(
            'monitoring_app_cpu_usage_percent',
            'CPU usage of the monitoring app itself'
        )
        
        self.system_memory_usage = Gauge(
            'monitoring_app_memory_usage_bytes',
            'Memory usage of the monitoring app itself'
        )
        
        self.collection_errors = Counter(
            'monitoring_collection_errors_total',
            'Total errors during metrics collection',
            ['service_name', 'error_type']
        )
        
        self.last_successful_collection = Gauge(
            'monitoring_last_successful_collection_timestamp',
            'Timestamp of last successful metrics collection',
            ['service_name']
        )
        
        # App info
        self.app_info = Info(
            'monitoring_app_info',
            'Monitoring application information'
        )
        
        self.app_info.info({
            'app_name': 'prometheus-monitoring',
            'monitored_services': ','.join([s.name for s in self.services]),
            'collection_interval': '10s',
            'pod_name': os.getenv('POD_NAME', 'monitoring-local'),
            'namespace': os.getenv('POD_NAMESPACE', 'default')
        })
        
        # Internal state
        self._collection_running = False
        self._last_metrics = {}
        
    async def start_collection(self, interval: float = 10.0):
        """Start continuous metrics collection"""
        if self._collection_running:
            logger.warning("Metrics collection is already running")
            return
            
        self._collection_running = True
        logger.info(f"Starting metrics collection with {interval}s interval")
        
        # Start background tasks
        asyncio.create_task(self._collect_service_metrics_loop(interval))
        asyncio.create_task(self._collect_system_metrics_loop(interval))
        
    async def stop_collection(self):
        """Stop metrics collection"""
        self._collection_running = False
        await self.client.aclose()
        logger.info("Stopped metrics collection")
        
    async def _collect_service_metrics_loop(self, interval: float):
        """Main loop for collecting metrics from monitored services"""
        while self._collection_running:
            try:
                await self._collect_all_service_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(interval)
                
    async def _collect_system_metrics_loop(self, interval: float):
        """Loop for collecting system metrics of the monitoring app itself"""
        while self._collection_running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_cpu_usage.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.system_memory_usage.set(memory.used)
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(interval)
                
    async def _collect_all_service_metrics(self):
        """Collect metrics from all configured services"""
        tasks = []
        for service in self.services:
            tasks.append(self._collect_service_metrics(service))
        
        # Run all collections concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for service, result in zip(self.services, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to collect metrics from {service.name}: {result}")
                self.collection_errors.labels(
                    service_name=service.name, 
                    error_type=type(result).__name__
                ).inc()
            else:
                self.last_successful_collection.labels(service_name=service.name).set(time.time())
                
    async def _collect_service_metrics(self, service: ServiceConfig):
        """Collect metrics from a specific service"""
        try:
            # Check if service is up
            is_up = await self._check_service_health(service)
            self.service_up.labels(
                service_name=service.name, 
                service_url=service.url
            ).set(1 if is_up else 0)
            
            if not is_up:
                return
                
            # Collect specific metrics based on service type
            if service.name == "ml-app":
                await self._collect_ml_app_metrics(service)
            elif service.name == "dispatcher":
                await self._collect_dispatcher_metrics(service)
                
        except Exception as e:
            logger.error(f"Error collecting metrics from {service.name}: {e}")
            self.collection_errors.labels(
                service_name=service.name, 
                error_type="collection_error"
            ).inc()
            raise
            
    async def _check_service_health(self, service: ServiceConfig) -> bool:
        """Check if a service is healthy"""
        try:
            start_time = time.time()
            
            # Try the health endpoint first, fallback to root
            for endpoint in [service.health_endpoint, "/"]:
                try:
                    response = await self.client.get(
                        f"{service.url}{endpoint}",
                        timeout=service.timeout
                    )
                    
                    duration = time.time() - start_time
                    self.service_response_time.labels(
                        service_name=service.name, 
                        endpoint=endpoint
                    ).observe(duration)
                    
                    if response.status_code < 400:
                        return True
                        
                except httpx.RequestError:
                    continue
                    
            return False
            
        except Exception as e:
            logger.error(f"Health check failed for {service.name}: {e}")
            return False
            
    async def _collect_ml_app_metrics(self, service: ServiceConfig):
        """Collect ML app specific metrics"""
        try:
            # Get app info and basic stats
            response = await self.client.get(f"{service.url}/")
            if response.status_code == 200:
                # For now, we increment prediction count based on service being alive
                # In a real scenario, you'd parse actual metrics from the ML service
                pass
                
        except Exception as e:
            logger.error(f"Error collecting ML app metrics: {e}")
            
    async def _collect_dispatcher_metrics(self, service: ServiceConfig):
        """Collect Dispatcher app specific metrics"""
        try:
            # Get dispatcher info
            response = await self.client.get(f"{service.url}/")
            if response.status_code == 200:
                # Here you could parse queue size if the dispatcher exposes it
                # For now, we'll simulate queue size monitoring
                pass
                
        except Exception as e:
            logger.error(f"Error collecting dispatcher metrics: {e}")
            
    async def get_service_status(self) -> Dict:
        """Get current status of all monitored services"""
        status = {}
        
        for service in self.services:
            try:
                is_healthy = await self._check_service_health(service)
                status[service.name] = {
                    "url": service.url,
                    "healthy": is_healthy,
                    "last_check": time.time()
                }
            except Exception as e:
                status[service.name] = {
                    "url": service.url,
                    "healthy": False,
                    "error": str(e),
                    "last_check": time.time()
                }
                
        return status
        
    def get_prometheus_metrics(self) -> str:
        """Get all Prometheus metrics in text format"""
        return generate_latest()
