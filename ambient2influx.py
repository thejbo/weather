#!/usr/bin/env python3
import sys
import requests
import yaml
from pathlib import Path
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

config_path = Path(__file__).parent / '.config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# InfluxDB configuration
token      = config['influx']['token']
org        = config['influx']['org']
bucket     = config['influx']['bucket']
influx_url = config['influx']['influx_url']

# Ambient Weather API configuration
api_endpoint    = config['ambient_weather']['api_endpoint']
api_key         = config['ambient_weather']['api_key']
application_key = config['ambient_weather']['application_key']
location        = config['ambient_weather']['location']

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

# Initialize InfluxDB client
client = InfluxDBClient(url=influx_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Disable SSL verification warnings if needed
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

try:
    response = requests.get(api_endpoint, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    for reading in data:
        point = Point('weather') \
            .tag('location', location) \
            .field('outdoor_temp_f', float(reading.get('tempf', 0))) \
            .field('indoor_temp_f', float(reading.get('tempinf', 0))) \
            .field('dew_point_f', float(reading.get('dewPoint', 0))) \
            .field('wind_speed_mph', float(reading.get('windspeedmph', 0))) \
            .field('wind_gust_mph', float(reading.get('windgustmph', 0))) \
            .field('wind_direction', float(reading.get('winddir', 0))) \
            .field('hourly_rain', float(reading.get('hourlyrainin', 0))) \
            .field('outdoor_humidity', float(reading.get('humidity', 0))) \
            .field('indoor_humidity', float(reading.get('humidityin', 0))) \
            .field('uv_index', float(reading.get('uv', 0))) \
            .field('solar_radiation', float(reading.get('solarradiation', 0))) \
            .field('absolute_pressure', float(reading.get('baromabsin', 0))) \
            .time(int(reading.get('dateutc', 0) / 1000), WritePrecision.S)
        write_api.write(bucket=bucket, org=org, record=point)
        print(point)

except requests.exceptions.RequestException as e:
    print(f'Error fetching ambient weather data: {e}')

client.close()
