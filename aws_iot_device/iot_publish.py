import time
import random
import ssl
import json
from paho.mqtt import client as mqtt


AWS_ENDPOINT = "a1oweg0z8cqmfg-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "RaspberryPiEmulator1"
TOPIC = "rpi/data"


# NOTE: These paths assume the folder is copied directly to /home/pi/
CA = "/home/pi/aws_iot_device/AmazonRootCA1.pem"
CERT = "/home/pi/aws_iot_device/certificate.pem.crt"
KEY = "/home/pi/aws_iot_device/private.pem.key"


def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    

client = mqtt.Client(client_id=CLIENT_ID)

client.tls_set(ca_certs=CA, certfile=CERT, keyfile=KEY, tls_version=ssl.PROTOCOL_TLSv1_2)

client.on_connect = on_connect
client.connect(AWS_ENDPOINT, 8883, 60)
client.loop_start()

print("starting to publish data")
print("press ctrl+c to stop")

try:
    message_count = 0
    while True:
        message_count += 1
        
        value = random.randint(0,100)
        payload = json.dumps({
            "device_id": CLIENT_ID,
            "timestamp": int(time.time()),
            "message_id": message_count,
            "sendor data": value,
            "status": "active",
            "message": "sensor reading"
        })
        
        print("Publishing:", payload)
        client.publish(TOPIC, payload, qos=1)
        time.sleep(5)
        
except KeyboardInterrupt:
    print("shutting down...")
    client.loop_stop()
    client.disconnect()
