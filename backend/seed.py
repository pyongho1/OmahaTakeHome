# backend/seed.py
from pathlib import Path
from dotenv import load_dotenv
import os
import json
from pathlib import Path
import MySQLdb as mysql
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

DATA_PATH = Path(__file__).parent.parent / "data" / "sample_data.json"

MYSQL_HOST = os.environ.get("MYSQL_HOST")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT"))
MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DB = os.environ.get("MYSQL_DB")

def get_conn():
    return mysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWORD,
        db=MYSQL_DB,
        charset="utf8mb4",
    )

SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS locations (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        country VARCHAR(64),
        latitude DOUBLE,
        longitude DOUBLE,
        region VARCHAR(128)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS metrics (
        id INT PRIMARY KEY,
        name VARCHAR(64) UNIQUE,
        display_name VARCHAR(128),
        unit VARCHAR(32),
        description VARCHAR(512)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS climate_data (
        id INT PRIMARY KEY,
        location_id INT NOT NULL,
        metric_id INT NOT NULL,
        date DATE NOT NULL,
        value DOUBLE NOT NULL,
        quality VARCHAR(32) NOT NULL,
        INDEX idx_cd_loc (location_id),
        INDEX idx_cd_metric (metric_id),
        INDEX idx_cd_date (date),
        CONSTRAINT fk_cd_loc FOREIGN KEY (location_id) REFERENCES locations(id),
        CONSTRAINT fk_cd_metric FOREIGN KEY (metric_id) REFERENCES metrics(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]

def ensure_schema(cur):
    for stmt in SCHEMA_SQL:
        cur.execute(stmt)

def seed_from_json(cur, path: Path = DATA_PATH):
    if not path.exists():
        raise FileNotFoundError(f"Sample data file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Locations
    loc_rows = [
        (
            row["id"],
            row.get("name"),
            row.get("country"),
            row.get("latitude"),
            row.get("longitude"),
            row.get("region"),
        )
        for row in payload.get("locations", [])
    ]
    if loc_rows:
        cur.executemany(
            """
            INSERT INTO locations (id, name, country, latitude, longitude, region)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE id = VALUES(id)
            """,
            loc_rows,
        )

    # Metrics
    met_rows = [
        (
            row["id"],
            row.get("name"),
            row.get("display_name"),
            row.get("unit"),
            row.get("description"),
        )
        for row in payload.get("metrics", [])
    ]
    if met_rows:
        cur.executemany(
            """
            INSERT INTO metrics (id, name, display_name, unit, description)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE id = VALUES(id)
            """,
            met_rows,
        )

    # Climate data
    cd_rows = [
        (
            row["id"],
            row["location_id"],
            row["metric_id"],
            row["date"],  # MySQL will parse 'YYYY-MM-DD' into DATE
            row["value"],
            row["quality"].lower(),
        )
        for row in payload.get("climate_data", [])
    ]
    if cd_rows:
        cur.executemany(
            """
            INSERT INTO climate_data (id, location_id, metric_id, date, value, quality)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE id = VALUES(id)
            """,
            cd_rows,
        )

def main():
    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_schema(cur)
        seed_from_json(cur)
        conn.commit()
        print("Seeding complete.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()