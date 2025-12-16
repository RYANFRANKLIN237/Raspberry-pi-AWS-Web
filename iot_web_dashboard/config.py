import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')


MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT')
MQTT_TOPIC = os.getenv('MQTT_TOPIC')
MQTT_CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'WebDashboard')

CA_PATH = 'AmazonRootCA1.pem'
CERT_PATH = 'certificate.pem.crt'
KEY_PATH = 'private.pem.key'