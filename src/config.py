import os
import yaml
from datetime import datetime, timezone
from dotenv import load_dotenv

#✅ Load environment variables from config/.env
load_dotenv(dotenv_path=os.path.join("config", ".env"))
#print("📦 Loading .env from:", os.path.join("config", ".env"))
#print("👉 URL being used:", config["openehr"]["url"])


def load_config(path=None):
    """
    Load configuration from config/settings.yml and replace ${ENV_VAR} with .env values.
    """
    if path is None:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, "config", "settings.yml")

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    def resolve_env(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_key = value[2:-1]
            return os.environ.get(env_key, "")
        return value

    def resolve_placeholders(d):
        if isinstance(d, dict):
            return {k: resolve_placeholders(resolve_env(v)) for k, v in d.items()}
        elif isinstance(d, list):
            return [resolve_placeholders(item) for item in d]
        else:
            return resolve_env(d)

    return resolve_placeholders(config)

def get_job_config(config):
    job_cfg = config.get("job", {})
    return {
        "db_path": job_cfg.get("db_path", "data/results.db"),
        "default_start": job_cfg.get("default_start", "2025-01-01T00:00:00Z"),
        "default_end": job_cfg.get("default_end"),
        "use_end_time": job_cfg.get("use_end_time", True),
        "interval_hours": int(job_cfg.get("interval_hours", 23)),
        "polling": job_cfg.get("polling", False),
        "polling_hours": int(job_cfg.get("polling_hours", 23))
    }

def get_email_templates(config, start_time, end_time=None):
    """
    Formats the subject and body using placeholders:
    {start_date}, {end_date}, {default_start}, {now}
    """
    email_cfg = config.get("email", {})
    subject_template = email_cfg.get("subject", "AQL Export: {start_date} to {end_date}")
    body_template = email_cfg.get("body", "Attached export from {start_date} to {end_date}")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    return (
        subject_template.format(
            start_date=start_time,
            end_date=end_time or "now",
            default_start=start_time,
            now=now
        ),
        body_template.format(
            start_date=start_time,
            end_date=end_time or "now",
            default_start=start_time,
            now=now
        )
    )
