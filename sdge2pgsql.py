#!/usr/bin/env python3
import csv
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

import psycopg2
import yaml

if len(sys.argv) < 2:
    print(f'Usage: {os.path.basename(sys.argv[0])} <csv_file_name>')
    sys.exit(1)

file_name = sys.argv[1]

config_path = Path(__file__).parent / '.config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# SDGE export configuration
data_path = config['sdge']['data_path']

# RDBMS configuration
servername = config['pgsql']['servername']
port       = config['pgsql']['port']
username   = config['pgsql']['username']
password   = config['pgsql']['password']
dbname     = config['pgsql']['dbname']

csv_path = os.path.join(data_path, file_name)

insert_sql = """
INSERT INTO sdge_usage (
    sample_timestamp,
    usage,
    generation
) VALUES (
    %s,
    %s,
    %s
)
ON CONFLICT (sample_timestamp)
    DO UPDATE SET
        usage=%s,
        generation=%s
"""

local_tz = ZoneInfo('America/Los_Angeles')

try:
    conn = psycopg2.connect(
        host=servername,
        port=port,
        user=username,
        password=password,
        dbname=dbname
    )
except psycopg2.Error as e:
    print(f'Error connecting to database: {e}')
    sys.exit(1)

try:
    with conn.cursor() as cursor:
        cursor.execute("SET timezone = 'America/Los_Angeles'")

        with open(csv_path, newline='') as csv_file:
            rows = list(csv.reader(csv_file))

        # First 14 rows are export headers, not readings
        for row in rows[14:]:
            if len(row) < 6:
                continue

            # Columns 1/2 hold the local date and time; store as UTC
            local_dt = datetime.strptime(
                f'{row[1]} {row[2]}', '%m/%d/%Y %I:%M %p'
            ).replace(tzinfo=local_tz)
            sample_timestamp = local_dt.astimezone(timezone.utc)

            usage      = float(row[4])
            generation = float(row[5])

            cursor.execute(
                insert_sql,
                (sample_timestamp, usage, generation, usage, generation)
            )

    conn.commit()

except OSError as e:
    conn.rollback()
    print(f'Error reading {csv_path}: {e}')
except ValueError as e:
    conn.rollback()
    print(f'Error parsing CSV data: {e}')
except psycopg2.Error as e:
    conn.rollback()
    print(f'Error writing sdge usage data: {e}')
finally:
    conn.close()
