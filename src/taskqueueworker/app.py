from flask import Flask, request, jsonify
from config import redis_client
import json
import uuid
from datetime import datetime

app = Flask(__name__)

TASK_QUEUE = 'task_queue'
TASK_STATUS = 'task_status:'

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return (jsonify({
            'status': 'healthy',
            'redis': 'connected'
        }), 200)
    except:
        return (jsonify({
            'status': 'unhealthy',
            'redis': 'disconnected'
        }), 503)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)