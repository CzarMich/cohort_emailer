FROM python:3.13-alpine

# Set working directory
WORKDIR /app

# Install dependencies for pip + compilation (alpine is minimal!)
RUN apk add --no-cache build-base libffi-dev openssl-dev

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY src/ ./src/
COPY config/settings.yml ./config/settings.yml
COPY config/.env.example ./config/.env

# Pre-compile to .pyc and remove .py
RUN python -m compileall -b ./src \
 && find ./src -name "*.py" -delete

# Create writable data folder and lock down source
RUN mkdir -p /app/data /app/logs && chmod -R a-w ./src

CMD ["python", "src/project.py"]
