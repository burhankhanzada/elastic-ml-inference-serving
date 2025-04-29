# Base Image
FROM python:3.11.12-slim

# Working directory
WORKDIR /app

# Copy requirements file first 
COPY requirements.txt .

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY frontend.py .

# Run the application
CMD ["streamlit", "run", "frontend.py"]
