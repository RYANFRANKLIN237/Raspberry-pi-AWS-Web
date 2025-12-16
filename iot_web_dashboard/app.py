from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key
import json
import time
from datetime import datetime
import config
import paho.mqtt.client as mqtt
import ssl
import threading
from queue import Queue
import os
from decimal import Decimal 

app = Flask(__name__)
CORS(app)

# ========== DYNAMODB CONNECTION ==========
# tokens, and secret keys expire every few hours make sure to get latest from learner lab 
try:
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        aws_session_token=config.AWS_SESSION_TOKEN
    )
    table = dynamodb.Table(config.DYNAMODB_TABLE)
    print(f"✓ Connected to DynamoDB table: {config.DYNAMODB_TABLE}")
except Exception as e:
    print(f"✗ DynamoDB connection failed: {e}")
    print("  Using mock data mode for historical data")
    table = None

# ========== MQTT CLIENT LIVE DATA ==========
mqtt_queue = Queue()
latest_message = None
mqtt_client = None

def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    print(f"✓ MQTT Connected with result code {rc}")
    if rc == 0:
        client.subscribe(config.MQTT_TOPIC)
        print(f"✓ Subscribed to topic: {config.MQTT_TOPIC}")
    else:
        print(f"✗ MQTT Connection failed: {rc}")



def on_message(client, userdata, msg):
    """MQTT message callback"""
    global latest_message
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        
        latest_message = {
            'topic': msg.topic,
            'payload': data,
            'timestamp': int(time.time()),
            'received_at': datetime.now().isoformat()
        }
        
        mqtt_queue.put(latest_message)
        print(f"MQTT: {data.get('message', 'New message')}")
        
    except Exception as e:
        print(f"Error processing MQTT: {e}")

def start_mqtt_client():
    """Start MQTT client in background"""
    global mqtt_client
    
    client = mqtt.Client(client_id=config.MQTT_CLIENT_ID)
   
    
    try:
        client.tls_set(
            ca_certs=config.CA_PATH,
            certfile=config.CERT_PATH,
            keyfile=config.KEY_PATH,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )

        
        client.on_connect = on_connect
        client.on_message = on_message
        
        client.connect(config.MQTT_ENDPOINT, 8883, 60)
        client.loop_start()
        mqtt_client = client
        print(f"✓ MQTT client started for {config.MQTT_ENDPOINT}")
        return True
        
    except Exception as e:
        print(f"✗ MQTT client failed: {e}")
        return False

# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/latest')
def get_latest():
    """Get latest MQTT message"""
    if latest_message:
        return jsonify({
            'success': True,
            'data': latest_message,
            'timestamp': latest_message['timestamp']
        })
    return jsonify({
        'success': False,
        'message': 'No MQTT messages yet'
    })

@app.route('/api/stream')
def stream():
    """Server-Sent Events for real-time MQTT"""
    def event_stream():
        while True:
            try:
                msg = mqtt_queue.get(timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
            except:
                yield ": heartbeat\n\n"
    
    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

@app.route('/api/historical')
def get_historical():
    """Get historical data from DynamoDB"""
    try:
        device_id = request.args.get('device_id', 'RaspberryPiEmulator1')
        hours = int(request.args.get('hours', 24))
        
        end_time = int(time.time())
        start_time = end_time - (hours * 3600)
        
        if not table:
            return jsonify({
                'success': False,
                'error': 'DynamoDB not connected'
            })
        
        response = table.query(
            KeyConditionExpression=Key('device_id').eq(device_id) & 
                                  Key('timestamp').between(start_time, end_time),
            Limit=100,
            ScanIndexForward=False
        )
        
        items = response.get('Items', [])
        formatted_data = []
        
        for item in items:

            sendor_data = item.get('sendor_data')
            if isinstance(sendor_data, Decimal):
                sendor_data = float(sendor_data)
            
            timestamp = item.get('timestamp')
            if isinstance(timestamp, Decimal):
                timestamp = int(timestamp)

            formatted_data.append({
                'device_id': item.get('device_id'),
                'timestamp': timestamp,
                'formatted_time': datetime.fromtimestamp(
                    timestamp
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'message': item.get('message', ''),
                'message_id': item.get('message_id', ''),
                'sendor_data': sendor_data,
                'status': item.get('status', 'active'),
                'value': sendor_data
            })
        
        return jsonify({
            'success': True,
            'count': len(formatted_data),
            'data': formatted_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stats')
def get_stats():
    """Get statistics"""
    try:
        if not table:
            return jsonify({
                'success': False,
                'message': 'DynamoDB not available'
            })
        
        end_time = int(time.time())
        start_time = end_time - 3600
        
        response = table.query(
            KeyConditionExpression=Key('device_id').eq('RaspberryPiEmulator1') & 
                                  Key('timestamp').between(start_time, end_time)
        )
        
        items = response.get('Items', [])
        
        if not items:
            return jsonify({
                'success': False,
                'message': 'No data'
            })
        
        values = []
        for item in items:
            val = item.get('sendor_data')
            if val is not None:
                try:
                    values.append(float(val))
                except:
                    pass
        
        stats = {
            'total_readings': len(items),
            'average_value': round(sum(values) / len(values), 2) if values else 0,
            'min_value': min(values) if values else 0,
            'max_value': max(values) if values else 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })



if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("Raspberry Pi IoT Dashboard")
    print("=" * 50)
    
    
    print("\nStarting MQTT client...")
    mqtt_started = start_mqtt_client()
    
    print("\nStarting web server on http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)