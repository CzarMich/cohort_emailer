# 🔄 AQL Email Dispatcher

This project allows automated execution of AQL queries against an openEHR server, dynamically filters the result set based on Cohort requirements, and routes the filtered data to email recipients via Microsoft Exchange.

---

## 📂 Project Features

- ✅ AQL Query Execution (with time filtering)
- ✅ SQLite Logging of Query Results & Metadata
- ✅ Rule-based Email Routing using Exchange API
- ✅ Scheduled / Test-friendly execution
- ✅ Dockerized for consistent deployment

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/alpamax/cohort_emailer.git
cd cohort_emailer
```

---

### 2. Create `.env` File

```bash
cp config/.env.example config/.env
```

Edit the file to provide your credentials:

```env
# openEHR Server
OPENEHR_URL=https://your_openehr.server/ehr/rest/v1
OPENEHR_USERNAME=openehr_user
OPENEHR_PASSWORD=your_admin_password

# Exchange Mail Server
EXCHANGE_SERVER=https://your.exchange.server/EWS/Exchange.asmx
EXCHANGE_USERNAME=your\domain-user
EXCHANGE_PASSWORD=your_password
EXCHANGE_SENDER=your_email@domain.com
```

---

### 3. Modify `config/settings.yml`

Update key parameters:

| Section              | Field              | Description                             |
|----------------------|--------------------|-----------------------------------------|
| `aql.base_query`     | `{start_time}`     | Required AQL placeholder                |
| `email.routing`      | `field`, `values`  | Routing rules per recipient             |
| `job.default_start`  | DateTime string    | When to begin data pulling              |
| `job.interval_hours` | Integer            | Time between query runs (in hours)      |
| `job.use_end_time`   | true / false       | Whether to inject `end_time` placeholder|

---

### 4. Run Locally (Dev Mode)

```bash
python src/project.py
```

Make sure you activate your virtual environment and have dependencies installed:

```bash
pip install -r requirements.txt
```

---

## 🐳 Docker Deployment

### Option 1: Run using Docker Hub image

You can run directly using the published image:

```bash
docker pull alpamaxeu/cohort_mailer:latest
```

```bash
docker run --rm \
  --env-file ./config/.env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config/settings.yml:/app/config/settings.yml \
  alpamaxeu/cohort_mailer:latest
```

### Option 2: Build Locally (Optional)

If you prefer building your own image:

```bash
docker build -t cohort_mailer .
```

Then run it as above.

---

### 🔧 Docker Compose (Recommended)

```yaml
version: '3.8'

services:
  aql_mailer:
    image: alpamaxeu/cohort_mailer:latest
    container_name: cohort_data_mailer
    env_file:
      - config/.env
    volumes:
      - ./data:/app/data
      - ./config/settings.yml:/app/config/settings.yml
      - ./config/.env:/app/config/.env
    labels:
      maintainer: "Michael Anywar <michael.anywar@alpamax.eu>"
      project: "AQL Email Dispatcher"
    restart: unless-stopped
```

Start with:

```bash
docker compose up -d
```

---

## 🔁 Scheduling with Cron

To run the job every 3 hours using Docker instead of the internal polling, set polling: false, then create the following cron:
bash# crontab -e
```cron
0 */3 * * * docker run --rm \
  --env-file /opt/cohort_emailer/config/.env \
  -v /opt/cohort_emailer/data:/app/data \
  -v /opt/cohort_emailer/config/settings.yml:/app/config/settings.yml \
  alpamaxeu/cohort_mailer:latest
```

Make sure paths are correct and Docker is available to the cron job.

---

## 💠 Maintained By

Michael Anywar  
💼 michael.anywar@alpamax.eu  
🌐 [alpamax.eu](https://www.alpamax.eu)

---
