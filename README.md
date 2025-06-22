# Elastic ML Inference Serving

**Cloud Computing Project - Summer Semester 2025**

## Team Members
- Muhammad Ozair
- Kamil Hassaan  
- Umair Hussain

## Project Overview

This project implements a scalable, containerized machine learning inference system for image classification using ResNet18. The system features a distributed architecture with intelligent request dispatching, queue management, and is designed for deployment on Kubernetes with custom autoscaling capabilities.

### Key Features
- **Fast Image Classification**: ResNet18 model with sub-0.5s latency target
- **Intelligent Request Dispatching**: Asynchronous queue-based request handling with worker pool
- **Producer-Consumer Architecture**: Decoupled request handling for better scalability
- **Containerized Deployment**: Docker containers for both ML service and dispatcher
- **Kubernetes Ready**: Complete K8s deployment configurations with services
- **Load Testing Framework**: Custom load tester with realistic workload patterns
- **Performance Monitoring**: Built-in queue size monitoring and response tracking

## Architecture

```
Load Tester → Dispatcher Service → ML Inference Service
     ↓              ↓                      ↓
  [Images]    [Queue + Workers]      [ResNet18 Model]
```

### Components

1. **ML Inference Service** (`ml_app/`)
   - FastAPI application serving ResNet18 model
   - Handles `/predict` endpoint for image classification
   - Pre-downloaded model weights for faster container startup
   - Runs on port 8000

2. **Dispatcher Service** (`dispatcher/`)
   - Request queue management using asyncio
   - Producer-consumer pattern with 4 background workers
   - Load balancing across ML service replicas
   - Runs on port 8001

3. **Load Tester** (`load_tester.py`)
   - Configurable workload patterns from `workload.txt`
   - Supports multiple image formats (PNG, JPG, JPEG)
   - Statistics tracking for classification results
   - Built on BarAzmoon framework

## Quick Start

### Prerequisites
- Python 3.9+
- Docker
- Kubernetes cluster (optional, for production deployment)
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/elastic-ml-inference.git
   cd elastic-ml-inference
   git clone https://github.com/EliSchwartz/imagenet-sample-images.git
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # Install PyTorch (CPU version)
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

### Running Locally

1. **Start ML Inference Service**
   ```bash
   cd ml_app
   uvicorn main:app --port 8000
   ```

2. **Start Dispatcher Service** (in new terminal)
   ```bash
   cd dispatcher
   uvicorn main:app --port 8001
   ```

3. **Run Load Test** (in new terminal)
   ```bash
   # Update image directory path in load_tester.py
   python load_tester.py
   ```

### Docker Deployment

1. **Build Docker images**
   ```bash
   # Build ML service
   docker build -f ml_app/Dockerfile -t ml-app:latest .
   
   # Build dispatcher service
   docker build -f dispatcher/Dockerfile -t dispatcher-app:latest .
   ```

2. **Run with Docker**
   ```bash
   # Run ML service
   docker run -p 8000:8000 ml-app:latest
   
   # Run dispatcher (in new terminal)
   docker run -p 8001:8001 -e ML_SERVICE_URL=http://host.docker.internal:8000 dispatcher-app:latest
   ```

### Kubernetes Deployment

1. **Deploy ML service**
   ```bash
   kubectl apply -f ml_app/ml-app-deployment.yaml
   ```

2. **Deploy dispatcher service**
   ```bash
   kubectl apply -f dispatcher/dispatcher-deployment.yaml
   ```

3. **Get service URLs**
   ```bash
   # Get dispatcher service URL for load testing
   kubectl get service dispatcher-service
   ```

## API Endpoints

### ML Inference Service (`localhost:8000`)
- `GET /` - Health check
- `POST /predict` - Image classification
  - Input: Image file (multipart/form-data)
  - Output: `{"prediction": "class_name: confidence%"}`

### Dispatcher Service (`localhost:8001`)
- `GET /` - Health check  
- `POST /add_to_queue` - Queue image for processing
  - Input: Image file (multipart/form-data)
  - Output: `{"prediction": "class_name: confidence%", "queue_size": int}`

## Load Testing

The load tester reads workload patterns from `workload.txt` and sends image classification requests at specified rates.

### Configuration
- **Workload Pattern**: Edit `workload.txt` with requests per second
- **Image Directory**: Update `image_dir` path in `load_tester.py`
- **Endpoint**: Configure dispatcher URL in load tester

### Sample Output
```
Image img_001.jpg: Classified as 'golden retriever' with 89.2% confidence
Worker 1 delivered result to request 12345678
Test Results: 450/500 successful requests (90.0%)
```

## Performance Characteristics

- **Target Latency**: Sub-0.5s response time
- **Queue Management**: Async queue with 4 concurrent workers
- **Scaling**: 3 ML service replicas in K8s deployment
- **Resource Limits**: 1GB memory, 1 CPU core per ML pod

## Project Status

### ✅ Completed
- FastAPI ML inference service with ResNet18
- Docker containerization for both services
- Kubernetes deployment configurations
- Async dispatcher with producer-consumer pattern
- Load testing framework with statistics
- Queue-based request management

### 🚧 In Progress
- Custom autoscaling algorithm
- Prometheus monitoring integration
- Redis-based queue for persistence
- Performance optimization

### 📋 Planned
- HPA (Horizontal Pod Autoscaler) comparison
- Advanced monitoring dashboards
- Stress testing scenarios

## Configuration

### Environment Variables
- `ML_SERVICE_URL`: ML inference service endpoint (default: `http://127.0.0.1:8000`)
- `PORT`: Service port numbers
- `PYTHONUNBUFFERED`: Enable real-time logging in K8s

### Resource Configuration
```yaml
resources:
  requests:
    cpu: 200m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

## Troubleshooting

### Common Issues
1. **Model download timeout**: ML service pre-downloads ResNet18 weights during build
2. **Queue bottleneck**: Dispatcher uses 4 workers, adjust based on ML service capacity
3. **Image format errors**: Ensure test images are PNG, JPG, or JPEG
4. **Service discovery**: Verify K8s service names match environment variables

### Debugging
- Check container logs: `kubectl logs -l app=ml-app`
- Monitor queue size via dispatcher API responses
- Verify service connectivity: `kubectl get services`

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.