#!/usr/bin/env python3
import requests
import yaml
from pathlib import Path
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

config_path = Path(__file__).parent / '.config.yaml'

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Envoy URLs
host_url   = config['envoy']['host_url']
host_url2  = config['envoy']['host_url2']
auth_basic = config['envoy']['auth_basic']

# InfluxDB configuration
token      = config['influx']['token']
org        = config['influx']['org']
bucket     = config['influx']['bucket']
influx_url = config['influx']['influx_url']

# Panel mapping
panel_array = {
    '202205098281': '1w',
    '202205136269': '1w',
    '202205148261': '1w',
    '202205151486': '1w',
    '202206028609': '1w',
    '202206028610': '1w',
    '202206030854': '1w',
    '202206030887': '1w',
    '202206034548': '1w',
    '202206035177': '1w',
    '202206035229': '1w',
    '202206035265': '1w',
    '202206035509': '1w',
    '202206035542': '1w',
    '202209027449': '1e',
    '202209028481': '1e',
    '202209029331': '1e',
    '202209029503': '1e',
    '202209029676': '1e',
    '202209034900': '1e',
    '202209038936': '1e',
    '202209041796': '1e',
    '202209042552': '1e',
    '202209043143': '1e',
    '202209048047': '1e',
    '202209050752': '1e',
    '202209050838': '1e',
    '202209058621': '1e',
    '202209058731': '1e',
    '202209059037': '1e',
}

# Initialize InfluxDB client
client = InfluxDBClient(url=influx_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Request headers
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {auth_basic}'
}

# Disable SSL verification warnings if needed
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# First request: get inverters data
try:
    response = requests.get(
        host_url,
        headers=headers,
        timeout=15,
        verify=False
    )
    response.raise_for_status()
    data = response.json()

    # Write inverter data to InfluxDB
    for inverter in data:
        serial_number = str(inverter.get('serialNumber', ''))
        panel_type = str(panel_array.get(serial_number, ''))

        point = Point('envoy') \
            .tag('serialNumber', serial_number) \
            .tag('panel_array', panel_type) \
            .field('lastReportWatts', float(inverter.get('lastReportWatts', 0))) \
            .time(inverter.get('lastReportDate'), WritePrecision.S)

        print(point)
        write_api.write(bucket=bucket, org=org, record=point)

except requests.exceptions.RequestException as e:
    print(f"Error fetching inverter data: {e}")

# Second request: get real-time production data
try:
    response = requests.get(
        host_url2,
        headers=headers,
        timeout=15,
        verify=False
    )
    response.raise_for_status()
    data = response.json()

    # Write real-time production data to InfluxDB
    production = data.get('production', [])
    if len(production) > 1:
        prod_data = production[1]
        point = Point('envoy_rt') \
            .field('wNow', float(prod_data.get('wNow', 0))) \
            .time(prod_data.get('readingTime'), WritePrecision.S)

        print(point)
        write_api.write(bucket=bucket, org=org, record=point)

except requests.exceptions.RequestException as e:
    print(f"Error fetching production data: {e}")

# Close client
client.close()
