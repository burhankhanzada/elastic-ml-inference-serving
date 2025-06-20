# Base Image
FROM python:3.11.12-slim

# Working directory
WORKDIR /app

# Copy requirements from parent directory
COPY requirements.txt .

# Install PyTorch CPU version
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# PRE-DOWNLOAD MODEL WEIGHTS (This is the fix!)
RUN python -c "from torchvision.models import resnet18; resnet18(weights='IMAGENET1K_V1')"

# Copy Python files from ml_app directory
COPY ml_app/main.py .
COPY ml_app/resnet_inference.py .

EXPOSE 8000 9001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]