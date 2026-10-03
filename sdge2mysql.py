#!/usr/bin/env python3
import csv
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

import pymysql
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
servername = config['mysql']['servername']
username   = config['mysql']['username']
password   = config['mysql']['password']
dbname     = config['mysql']['dbname']

csv_path = os.path.join(data_path, file_name)

insert_sql = """
REPLACE INTO `sdge_usage` (
    `sample_timestamp`,
    `usage`,
    `generation`
) VALUES (
    %s, %s, %s
)
"""

local_tz = ZoneInfo('America/Los_Angeles')

try:
    conn = pymysql.connect(
        host=servername,
        user=username,
        password=password,
        database=dbname,
        autocommit=True
    )
except pymysql.MySQLError as e:
    print(f'Error connecting to database: {e}')
    sys.exit(1)

try:
    with open(csv_path, newline='') as csv_file:
        rows = list(csv.reader(csv_file))

    with conn.cursor() as cursor:
        # First 14 rows are export headers, not readings
        for row in rows[14:]:
            if len(row) < 6:
                continue

            # Columns 1/2 hold the local date and time; store as UTC
            local_dt = datetime.strptime(
                f'{row[1]} {row[2]}', '%m/%d/%Y %I:%M %p'
            ).replace(tzinfo=local_tz)

            sample_timestamp = local_dt.astimezone(
                timezone.utc
            ).strftime('%Y-%m-%d %H:%M:%S')

            record = (
                sample_timestamp,   # sample_timestamp
                float(row[4]),      # usage
                float(row[5]),      # generation
            )

            cursor.execute(insert_sql, record)
            print(local_dt, sample_timestamp, insert_sql, record)

except OSError as e:
    print(f'Error reading {csv_path}: {e}')
except ValueError as e:
    print(f'Error parsing CSV data: {e}')
except pymysql.MySQLError as e:
    print(f'Error writing sdge usage data: {e}')
finally:
    conn.close()
