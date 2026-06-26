# Use a lightweight official Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file if you have one
COPY requirements.txt .

# Install dependencies directly to keep it simple
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY main.py .

# Expose the port FastAPI will run on
EXPOSE 8000

# Run the API gateway
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]