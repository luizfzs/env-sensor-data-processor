from influxdb import InfluxDBClient
from datetime import datetime
import json
import pika
import pytz


def get_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)


def process_event(ch, method, properties, body):
    print(f'Message: {body}')
    json_reading = json.loads(body.decode('UTF-8'))
    insert_sensor_read(json_reading)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def insert_sensor_read(sensor_reading):
    utc_timestamp = sensor_reading['timestamp']
    reading_time = datetime.utcfromtimestamp(utc_timestamp)
    try:
        # sometimes, the sensor sends an incorrect timestamp e.g. 3, 5, ...
        # when that happens, the timezone conversion fails.
        # on those cases, i'll just ignore that data point.
        reading_time.astimezone(timezone)
    except OSError:
        return

    data_point = {
        "measurement": config["influxdb"]["measurement"],
        "time": reading_time,
        "fields": {
            "temperature": sensor_reading['temperature'],
            "humidity": sensor_reading['humidity'],
            "heatIndex": sensor_reading['heatIndex']
        }
    }
    influxdb_client.write_points([data_point])


config = get_config()

timezone = pytz.timezone(config['general']['timezone'])

influxdb_client = InfluxDBClient(
    host=config["influxdb"]["host"],
    port=config["influxdb"]["port"],
    database=config["influxdb"]["database"]
)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=config["rabbitmq"]["host"],
        port=config["rabbitmq"]["port"],
        credentials=pika.PlainCredentials(
            config["rabbitmq"]["user"],
            config["rabbitmq"]["pass"]
        )
    )
)

channel = connection.channel()

channel.basic_consume(
    queue=config["rabbitmq"]["consume_from_queue"],
    on_message_callback=process_event
)

channel.start_consuming()
