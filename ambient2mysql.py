#!/usr/bin/env python3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pymysql
import requests
import yaml

config_path = Path(__file__).parent / '.config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Ambient Weather API configuration
api_endpoint    = config['ambient_weather']['api_endpoint']
api_key         = config['ambient_weather']['api_key']
application_key = config['ambient_weather']['application_key']
device          = config['ambient_weather']['device_mac']

# RDBMS configuration
servername = config['mysql']['servername']
username   = config['mysql']['username']
password   = config['mysql']['password']
dbname     = config['mysql']['dbname']

params = {
    'apiKey': api_key,
    'applicationKey': application_key,
    'limit': 2,
}

headers = {
    'Accept': 'application/json',
    'Accept-Language': 'en-US',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

insert_sql = """
REPLACE INTO `ambient_weather` (
    `sample`,
    `outdoor_temp_f`,
    `indoor_temp_f`,
    `dew_point_f`,
    `wind_speed_mph`,
    `wind_gust_mph`,
    `wind_direction`,
    `hourly_rain`,
    `outdoor_humidity`,
    `indoor_humidity`,
    `uv_index`,
    `solar_radiation`,
    `absolute_pressure`,
    `device_mac`
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
    response = requests.get(api_endpoint, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    with conn.cursor() as cursor:
        for reading in data:
            sample_date = datetime.fromtimestamp(
                int(reading.get('dateutc', 0)) / 1000, tz=timezone.utc
            ).strftime('%Y-%m-%d %H:%M:%S')

            record = (
                sample_date,                      # sample
                float(reading.get('tempf', 0)),       # outdoor_temp_f
                float(reading.get('tempinf', 0)),     # indoor_temp_f
                float(reading.get('dewPoint', 0)),    # dew_point_f
                float(reading.get('windspeedmph', 0)),# wind_speed_mph
                float(reading.get('windgustmph', 0)), # wind_gust_mph
                float(reading.get('winddir', 0)),     # wind_direction
                float(reading.get('hourlyrainin', 0)),# hourly_rain
                float(reading.get('humidity', 0)),    # outdoor_humidity
                float(reading.get('humidityin', 0)),  # indoor_humidity
                float(reading.get('uv', 0)),          # uv_index
                float(reading.get('solarradiation', 0)), # solar_radiation
                float(reading.get('baromabsin', 0)),  # absolute_pressure
                device,                              # device MAC addr
            )

            cursor.execute(insert_sql, record)

except requests.exceptions.RequestException as e:
    print(f'Error fetching ambient weather data: {e}')
except pymysql.MySQLError as e:
    print(f'Error writing ambient weather data: {e}')
finally:
    conn.close()
