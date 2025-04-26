#!/bin/bash

# 🟢 AQL Email Dispatcher - Docker Run Script
# Ensures required config files are present before launching the container

# Resolve absolute paths
PROJECT_DIR=$(pwd)
ENV_FILE="$PROJECT_DIR/config/.env"
SETTINGS_FILE="$PROJECT_DIR/config/settings.yml"
DATA_DIR="$PROJECT_DIR/data"

# 🔍 Check for required files
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Missing .env file at $ENV_FILE"
  exit 1
fi

if [ ! -f "$SETTINGS_FILE" ]; then
  echo "❌ Missing settings.yml at $SETTINGS_FILE"
  exit 1
fi

# 🐳 Run Docker container
docker run --rm \
  --env-file "$ENV_FILE" \
  -v "$SETTINGS_FILE":/app/config/settings.yml \
  -v "$ENV_FILE":/app/config/.env \
  -v "$DATA_DIR":/app/data \
  aql-mailer

# 🛠 Maintained by Michael Anywar | michael.anywar@uksh.de
