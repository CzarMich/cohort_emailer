from src.config import load_config, get_job_config, get_email_templates
from src.utils import (
    init_db,
    get_last_run_time,
    update_last_run_time,
    run_aql,
    init_dynamic_table,
    store_dynamic_results,
    query_results_by_field_value,
    export_results_to_csv,
    send_email,
    clear_result_table,
    log_run_metadata,
    construct_query_from_settings
)
from datetime import datetime, timedelta, timezone

def run_job():
    config = load_config()
    job_cfg = get_job_config(config)

    db_path = job_cfg["db_path"]
    default_start = job_cfg["default_start"]
    default_end = job_cfg.get("default_end")  # optional
    interval_hours = job_cfg.get("interval_hours", 24)

    init_db(db_path)

    # Determine time window
    last_run = get_last_run_time(db_path, default_start)
    start_dt = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
    start_time = start_dt.replace(microsecond=0).isoformat() + "Z"
    end_time = default_end if job_cfg.get("use_end_time", False) else None

    # Build query
    aql_query = construct_query_from_settings(config, start_time, end_time)
    #print(f"\n🔍 Running AQL from {start_time} to {end_time or '[no end_time]'}\n")
    #print(f"📎 AQL Payload:\n{aql_query}\n")
    #print(f"🔗 AQL URL: {config['openehr']['url'].rstrip('/')}/query")

    columns, rows = run_aql(
        aql_query,
        config["openehr"]["url"],
        config["openehr"]["username"],
        config["openehr"]["password"]
    )

    if rows:
        init_dynamic_table(columns, db_path)
        store_dynamic_results(columns, rows, db_path)

        # Email metadata
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        exchange = config["email"]["exchange"]
        subject_template = config["email"].get("subject", "AQL Export: {start_date} to {end_date}")
        body_template = config["email"].get("body", "Export from {start_date} to {end_date}")

        subject = subject_template.format(
            start_date=start_time,
            end_date=end_time or "now",
            default_start=start_time,
            now=now
        )
        body = body_template.format(
            start_date=start_time,
            end_date=end_time or "now",
            default_start=start_time,
            now=now
        )

        for rule in config["email"]["routing"]:
            field = rule["field"]
            values = rule["values"]
            recipient = rule["recipient"]

            all_matches = []
            print(f"\n📬 Routing rule for: {recipient} | Field: {field} | Patterns: {values}")
            for value in values:
                matches = query_results_by_field_value(db_path, field, value)
                print(f"   🔸 {field} = '{value}' → {len(matches)} match(es)")
                all_matches.extend(matches)

            # Deduplicate rows by primary key (e.g. composition_id)
            if all_matches:
                seen = set()
                unique_matches = []
                col_index = [col["name"] for col in columns].index("composition_id") if "composition_id" in [col["name"] for col in columns] else 0
                for row in all_matches:
                    row_id = row[col_index]
                    if (recipient, row_id) not in seen:
                        seen.add((recipient, row_id))
                        unique_matches.append(row)

                csv_data = export_results_to_csv(columns, unique_matches)
                send_email(exchange, recipient, csv_data, subject, body)
                print(f"✅ Email sent to {recipient} with {len(unique_matches)} row(s)")
            else:
                print(f"⚠️ No matches found for {recipient} → Skipping email.")

        log_run_metadata(db_path, start_time, end_time or "[none]", len(rows))
        clear_result_table(db_path)
    else:
        print("No new results.")

    # Update last run time for next execution
    next_start_dt = datetime.now(timezone.utc) + timedelta(hours=interval_hours)
    next_start_time = next_start_dt.replace(microsecond=0).isoformat()
    update_last_run_time(db_path, next_start_time)

if __name__ == "__main__":
    run_job()
