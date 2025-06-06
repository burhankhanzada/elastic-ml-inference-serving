# Base Image
FROM python:3.11.12-slim

# Working directory
WORKDIR /app

# Copy requirements file first
COPY requirements.txt .

# Copy the Python files from ml_app directory
COPY ml_app/main.py .
COPY ml_app/resnet_inference.py .

# Install PyTorch CPU version
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]