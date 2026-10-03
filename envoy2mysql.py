#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime, timezone

import pymysql
import requests
import yaml

config_path = Path(__file__).parent / '.config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Envoy URLs
host_url   = config['envoy']['host_url']
auth_basic = config['envoy']['auth_basic']

# RDBMS configuration
servername = config['mysql']['servername']
username   = config['mysql']['username']
password   = config['mysql']['password']
dbname     = config['mysql']['dbname']

# Request headers
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {auth_basic}'
}

insert_sql = """
REPLACE INTO `envoy` (
    `lastReportDate`,
    `serialNumber`,
    `lastReportWatts`
) VALUES (
    %s, %s, %s
)
"""

# Disable SSL verification warnings if needed
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

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
    response = requests.get(
        host_url,
        headers=headers,
        timeout=15,
        verify=False
    )
    response.raise_for_status()
    data = response.json()

    with conn.cursor() as cursor:
        for inverter in data:
            sample_date = datetime.fromtimestamp(
                int(inverter.get('lastReportDate', 0)), tz=timezone.utc
            ).strftime('%Y-%m-%d %H:%M:%S')

            record = (
                sample_date,                            # lastReportDate
                str(inverter.get('serialNumber', '')),   # serialNumber
                float(inverter.get('lastReportWatts', 0))# lastReportWatts
            )

            cursor.execute(insert_sql, record)
            print(f'New record for {sample_date} created successfully')

except requests.exceptions.RequestException as e:
    print(f'Error fetching inverter data: {e}')
except pymysql.MySQLError as e:
    print(f'Error writing inverter data: {e}')
finally:
    conn.close()
