# Base Image
FROM python:3.11.12-slim

# Working directory
WORKDIR /app

COPY requirements.txt .
COPY dispatcher/main.py .
COPY dispatcher/dispatcher.py .

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8001 9000
# Run the application
CMD ["uvicorn", "dispatcher_api:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
