# Elastic ML Inference Serving

### This is an APL project for Cloud Computing - Summer Semester 2025:

### Group Members:
1. Muhammad Ozair
2. Kamil Hassaan
3. Umair Hussain

## Project Overview

This project implements an autoscaling system for image classification in a Kubernetes environment. We compare custom autoscaling strategies with Kubernetes' native Horizontal Pod Autoscaler (HPA).

The system features:
- Fast inference with ResNet18 model
- Smart request dispatching
- Custom autoscaling algorithm
- Real-time performance monitoring

Our goal is to achieve sub-0.5s latency while optimizing resource usage.

## Installation Guide

### Prerequisites

- Python 3.9+ 
- pip (Python package manager)
- Docker (for containerization)
- Kubernetes cluster (for deployment)
- Git (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/elastic-ml-inference.git
cd elastic-ml-inference
```

### Step 2: Set Up Python Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# For Windows
venv\Scripts\activate
# For macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

### Run Locally (Development Mode)

1. Start the FastAPI backend:

```bash
# In the project root directory
uvicorn main:app --reload
```

2. In a new terminal, start the Streamlit frontend:

```bash
# Make sure your virtual environment is activated
streamlit run frontend.py
```

3. Open your web browser and navigate to:
   - FastAPI backend: http://127.0.0.1:8000/
   - Streamlit frontend: http://localhost:8501/

## System Architecture

Our system consists of:
- **Frontend**: Streamlit web interface
- **Backend**: FastAPI service for handling requests
- **ML Model**: ResNet18 for image classification

## License

[MIT License](LICENSE)    

# *TODOs*:
    1. Create a FastAPI app that serves the `ResNet18` model for image classification.
    2. Containerize the FastAPI app:
        - Create a `DockerFile`
            1. Created a dockerfile for FastAPI app; next is to create docker file for Streamlit app.
            2. The Frontend (Streamlit app) and Backend (FastAPI app) will be ran in two separate containers and a network will be made for these to communicate -> Possible solution to this is using docker compose which requires us to use a *.yaml* file.
    3. Further tasks -> *`TBD`*
        