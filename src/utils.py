# utils.py
import sqlite3
import requests
import csv
import os
from io import StringIO
from exchangelib import Credentials, Account, Message, FileAttachment, Configuration, DELEGATE


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_state (
            id INTEGER PRIMARY KEY,
            last_run TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            rows_fetched INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def get_last_run_time(db_path, default_start):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT last_run FROM job_state WHERE id = 1;")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default_start


def update_last_run_time(db_path, run_time):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO job_state (id, last_run) VALUES (1, ?);", (run_time,))
    conn.commit()
    conn.close()


def log_run_metadata(db_path, start_time, end_time, row_count):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO job_log (start_time, end_time, rows_fetched)
        VALUES (?, ?, ?);
        """,
        (start_time, end_time, row_count)
    )
    conn.commit()
    conn.close()


def construct_query_from_settings(config: dict, start_time: str, end_time: str = None) -> str:
    aql_template = config["aql"]["base_query"]
    use_end_time = config.get("job", {}).get("use_end_time", True)
    aql_query = aql_template.replace("{start_time}", start_time)
    if use_end_time and end_time:
        aql_query = aql_query.replace("{end_time}", end_time)
    else:
        aql_query = aql_query.replace("AND v/commit_audit/time_committed/value < '{end_time}'", "")

    return aql_query


def run_aql(aql_query, ehr_url, username, password):
    url = ehr_url.rstrip("/") + "/query"
    headers = {"Content-Type": "application/json"}
    payload = {"aql": aql_query}

    #print("🔗 AQL URL:", url)
    #print("📤 AQL Payload:", aql_query)

    try:
        response = requests.post(url, auth=(username, password), headers=headers, json=payload)
        response.raise_for_status()

        try:
            result_json = response.json()
        except ValueError:
            print("⚠️ Response could not be parsed as JSON.")
            print("🔻 Raw response text:")
            print(response.text)
            return [], []

        result_set = result_json.get("resultSet", [])

        if not result_set:
            print("✅ No records found.")
            return [], []

        columns = list(result_set[0].keys())
        rows = [[row.get(col) for col in columns] for row in result_set]
        return [{"name": col} for col in columns], rows

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ AQL HTTP error: {http_err}\n{response.text}")
        return [], []
    except Exception as e:
        print(f"❌ AQL unexpected error: {e}")
        return [], []


def init_dynamic_table(columns, db_path, table_name="results"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    fields_sql = ", ".join([f'"{col["name"]}" TEXT' for col in columns])
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({fields_sql});"
    cursor.execute(create_sql)
    conn.commit()
    conn.close()


def store_dynamic_results(columns, rows, db_path, table_name="results"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    col_names = [col["name"] for col in columns]
    placeholders = ", ".join(["?"] * len(col_names))
    insert_sql = f'INSERT INTO {table_name} ({", ".join(col_names)}) VALUES ({placeholders})'
    for row in rows:
        cursor.execute(insert_sql, row)
    conn.commit()
    conn.close()


def query_results_by_field_value(db_path, field, value, table_name="results"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if field exists
    cursor.execute(f"PRAGMA table_info({table_name})")
    fields = [row[1] for row in cursor.fetchall()]
    if field not in fields:
        raise ValueError(f"Field '{field}' not found in result table.")

    # Wildcard support
    if "*" in value:
        pattern = value.replace("*", "%")
        cursor.execute(f"SELECT * FROM {table_name} WHERE {field} LIKE ?", (pattern,))
    else:
        cursor.execute(f"SELECT * FROM {table_name} WHERE {field} = ?", (value,))

    rows = cursor.fetchall()
    conn.close()
    return rows



def export_results_to_csv(columns, rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([col["name"] for col in columns])
    writer.writerows(rows)
    return output.getvalue()


def send_email(exchange_config, recipient, csv_data, subject, body):
    creds = Credentials(
        username=exchange_config["username"],
        password=exchange_config["password"]
    )

    config = Configuration(
        server=exchange_config["server"].replace("https://", "").replace("/EWS/Exchange.asmx", ""),
        credentials=creds
    )

    account = Account(
        primary_smtp_address=exchange_config["sender"],
        config=config,
        autodiscover=False,
        access_type=DELEGATE
    )

    m = Message(
        account=account,
        subject=subject,
        body=body,
        to_recipients=[recipient]
    )
    attachment = FileAttachment(
        name="results.csv",
        content=csv_data.encode("utf-8")
    )
    m.attach(attachment)
    m.send()


def clear_result_table(db_path, table_name="results"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name}")
    conn.commit()
    conn.close()
