# 🔄 AQL Email Dispatcher

This project allows automated execution of AQL queries against an openEHR server, dynamically filters the result set based on Cohort requirements and routes the filtered data to email recipients via Microsoft Exchange.

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
git clone https://github.com/your-org/aql-mailer.git
cd aql-mailer
```

---

### 2. Create `.env` File

Copy the example and fill in your credentials:

```bash
cp config/.env.example config/.env
```

Edit `config/.env` and set values:

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

Update the following to match your use case:

| Section              | Field              | Description                             |
|----------------------|--------------------|-----------------------------------------|
| `aql.base_query`     | `{start_time}`     | Required AQL placeholder                |
| `email.routing`      | `field`, `values`  | Routing rules per recipient             |
| `job.default_start`  | DateTime string    | When to begin data pulling              |
| `job.interval_hours` | Integer            | Time between query runs (in hours)      |
| `job.use_end_time`   | true / false       | Whether to inject end_time placeholder  |

---

### 4. Run Locally

Activate your Python environment and run:

```bash
python project.py
```

---

## 🐳 Docker Deployment

### 1. Build Docker Image

```bash
docker build -t aql-mailer .
```

### 2. Run Docker Container

```bash
docker run --env-file config/.env aql-mailer
```

If you want to persist the SQLite database between runs:

```bash
docker run --env-file config/.env -v $(pwd)/data:/app/data aql-mailer
```

---

### Optional: Use Docker Compose

You can use the included `docker-compose.yml` to simplify deployment:

```yaml
version: '3.8'
services:
  aql_mailer:
    build: .
    container_name: cohort_data_mailer
    env_file:
      - config/.env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

Then run:

```bash
docker compose up --build
```

---

## 🔁 Scheduling with Cron

To schedule the job every 3 hours, you can add a cron entry like:

```cron
0 */3 * * * cd /path/to/aql-mailer && docker run --rm --env-file config/.env -v $(pwd)/data:/app/data aql-mailer
```

Make sure your cron environment has access to Docker.

---

## 📄 Requirements

Install dependencies manually (if not using Docker):

```bash
pip install -r requirements.txt
```

---

## 💠 Maintained By

Michael Anywar  
michael.anywar@alpamax.eu

---