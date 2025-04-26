import json
from datetime import datetime, timezone
from src.config import load_config, get_job_config, get_email_templates
from src.utils import (
    run_aql,
    construct_query_from_settings,
    init_db,
    init_dynamic_table,
    store_dynamic_results,
    export_results_to_csv,
    send_email,
    query_results_by_field_value,
    clear_result_table
)

def run_test_aql():
    config = load_config()
    job_cfg = get_job_config(config)

    db_path = job_cfg["db_path"]
    start_time = job_cfg["default_start"]
    end_time = job_cfg["default_end"] if job_cfg.get("use_end_time", False) else None

    print("Using credentials:")
    print("URL:", config["openehr"]["url"])
    print("Username:", config["openehr"]["username"])
    print("Password:", "*" * len(config["openehr"]["password"]))

    # Build AQL
    aql_query = construct_query_from_settings(config, start_time, end_time)
    #print("🔍 AQL Query:\n", aql_query)

    # Run query
    columns, rows = run_aql(
        aql_query,
        config["openehr"]["url"],
        config["openehr"]["username"],
        config["openehr"]["password"]
    )

    if not rows:
        print("⚠️ No results returned.")
        return

    print(f"✅ Fetched {len(rows)} records.")
    result_json = [dict(zip([col["name"] for col in columns], row)) for row in rows]
    with open("aql_response.json", "w") as f:
        json.dump(result_json, f, indent=2)

    init_db(db_path)
    init_dynamic_table(columns, db_path)
    store_dynamic_results(columns, rows, db_path)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    subject, body = get_email_templates(config, start_time, end_time)

    exchange = config["email"]["exchange"]
    for rule in config["email"]["routing"]:
        field = rule["field"]
        values = rule["values"]
        recipient = rule["recipient"]

        all_matches = []
        for value in values:
            matches = query_results_by_field_value(db_path, field, value)
            all_matches.extend(matches)

        if all_matches:
            csv_data = export_results_to_csv(columns, all_matches)
            send_email(exchange, recipient, csv_data, subject, body)
            print(f"📤 Sent results where {field} in {values} to {recipient}")

    clear_result_table(db_path)

if __name__ == "__main__":
    run_test_aql()
