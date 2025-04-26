# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies first (to cache better)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and config
COPY src/ ./src/
COPY config/settings.yml ./config/settings.yml

# Provide fallback .env file only if not mounted externally
COPY config/.env.example ./config/.env

# Precompile all Python files in src to .pyc and remove source .py files
RUN python -m compileall -b ./src \
 && find ./src -name "*.py" -delete

# Create a writable data folder, but lock down source code
RUN mkdir -p /app/data && chmod -R a-w ./src

# Default command
CMD ["python", "src/project.py"]
