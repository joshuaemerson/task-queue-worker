from flask import Flask, request, jsonify
from config import redis_client, TASK_QUEUE, TASK_STATUS
import json
import uuid
from datetime import datetime

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return jsonify({
            'status': 'healthy',
            'redis': 'connected'
        }), 200
    except:
        return jsonify({
            'status': 'unhealthy',
            'redis': 'disconnected'
        }), 503

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task and add it to the queue"""
    try:
        data = request.get_json()

        if not data or 'type' not in data:
            return jsonify({
                'error': 'Type task is required'
            }), 400
        
        # Validate data for email task
        if data['type'].lower() == 'email':
            if not data['data']:
                return jsonify({
                    'error': 'Property \'data\' is required'
                }), 400
            if not data['data'].get('recipient', ''):
                return jsonify({
                    'error': 'Expecting property \'recipient\' in \'data\''
                }), 400
            if not data['data'].get('content', ''):
                return jsonify({
                    'error': 'Expecting property \'content\' in \'data\''
                }), 400
            if type(data['data']['recipient']) != str or type(data['data']['content']) != str:
                return jsonify({
                    'error': 'Expecting property \'content\' in \'data\''
                }), 422
        
        task_id = uuid.uuid4()
        task = {
            'id': str(task_id),
            'type': data['type'],
            'data': data.get('data', {}),
            'created_at': datetime.now().isoformat(),
            'status': 'queued'
        }

        # Store task status
        redis_client.set(f'{TASK_STATUS}{task_id}', json.dumps(task))

        # Add task to queue
        redis_client.rpush(f'{TASK_QUEUE}', json.dumps(task))

        return jsonify({
            'task_id': task_id,
            'status': 'queued',
            'message': 'Task created successfully'
        }), 201

    except Exception as error:
        return jsonify({
            'status': 'unhealthy', 
            'error': f'Internal Server Error: {error}'
        }), 500
    
@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id: uuid.UUID):
    """Get the status of a specific task"""
    try:
        task_data = redis_client.get(f'{TASK_STATUS}{task_id}')

        if not task_data:
            return jsonify({
                'error': 'Task not found'
            }), 404
        
        task = json.loads(task_data)

        return jsonify(task), 200
    except Exception as error:
        return jsonify({
            'status': 'unhealthy', 
            'error': f'Internal Server Error: {error}'
        }), 500

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """List (at most) the last 100 tasks"""
    try:
        keys = redis_client.keys(f'{TASK_STATUS}*')
        tasks = []

        for key in keys:
            task_data = redis_client.get(key)
            if task_data:
                tasks.append(json.loads(task_data))
        
        return jsonify({
            'tasks': tasks,
            'count': len(tasks)
        }), 200
    except Exception as error:
        return jsonify({
            'status': 'unhealthy', 
            'error': f'Internal Server Error: {error}'
        }), 500
    
@app.route('/queue/stats', methods=['GET'])
def queue_stats():
    """Get queue statistics"""
    try:
        queue_length = redis_client.llen(TASK_QUEUE)

        return jsonify({
            'queue_length': queue_length,
            'total_tasks': len(redis_client.keys(f'{TASK_STATUS}*'))
        }), 200

    except Exception as error:
        return jsonify({
            'status': 'unhealthy', 
            'error': f'Internal Server Error: {error}'
        }), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)