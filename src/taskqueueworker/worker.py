from config import redis_client, TASK_STATUS, TASK_QUEUE
import redis
from utils import send_email
import json
import time
from datetime import datetime
import traceback

def process_task(task):
    """Process different types of tasks"""
    task_type = task.get('type')
    task_data = task.get('data', {})
    task_id = task['id']

    print(f"Processing task {task_id} of type {task_type}")

    if task_type.lower() == 'email':
        send_email(task_data.get('subject', ''), task_data['recipient'], task_data['content'])
        result = f"Email sent to {task_data['recipient']}"
    
    # Include other tasks in the future

    return result

def update_task_status(task_id, status, result=None):
    """Update task status in Redis"""
    try:
        task_key = f'{TASK_STATUS}{task_id}'
        task_data = redis_client.get(task_key)
        
        if task_data:
            if isinstance(task_data, bytes):
                task_data = task_data.decode('utf-8')
            
            task = json.loads(task_data)
            task['status'] = status
            task['updated_at'] = datetime.utcnow().isoformat()
            
            if result:
                task['result'] = result
            
            redis_client.set(task_key, json.dumps(task))
        else:
            print(f"Warning: Task {task_id} not found in Redis")
    except Exception as e:
        print(f"Error updating task status: {e}")
        traceback.print_exc()

def main():
    """Main worker loop"""
    print("Worker started. Waiting for tasks...")
    
    while True:
        try:
            # Block and wait for a task (timeout 1 second)
            result = redis_client.blpop(TASK_QUEUE, timeout=1)
            
            # blpop returns None when timeout expires with no data
            if result is None:
                continue
                
            # Unpack the result - should be (queue_name, task_json)
            queue_name, task_json = result
            
            # Parse the task JSON
            if isinstance(task_json, bytes):
                task_json = task_json.decode('utf-8')
            
            task = json.loads(task_json)
            
            print(f"\nReceived task: {task['id']}")
            
            # Update status to processing
            update_task_status(task['id'], 'processing')
            
            try:
                # Process the task
                result = process_task(task)
                
                # Update status to completed
                update_task_status(task['id'], 'completed', result)
                print(f"Task {task['id']} completed: {result}")
                
            except Exception as e:
                # Update status to failed
                error_msg = f"Error: {str(e)}"
                update_task_status(task['id'], 'failed', error_msg)
                print(f"Task {task['id']} failed: {error_msg}")
            
        except redis.ConnectionError:
            print("Redis connection error. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nWorker shutting down...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            print(f"Full traceback:")
            traceback.print_exc()
            time.sleep(1)

if __name__ == '__main__':
    main()
