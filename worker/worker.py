import os
import json
import requests
from celery import Celery
import importlib.util
import sys

# Add the api directory to the Python path so we can import modules from it
api_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api')
sys.path.append(api_path)

# Import correction modules
from corr.audio import audio_correct
from corr.prints import prints_correct
from corr.slides import slides_correct
from corr.video import vhs_correct

# Configure Celery
app = Celery('worker')
app.conf.broker_url = os.environ.get('CELERY_BROKER_URL', 'amqp://miniware:miniware_password@localhost:5672//')
app.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60  # 30 minutes

# Dictionary mapping media types to their correction functions
CORRECTION_FUNCTIONS = {
    'audio': audio_correct.correct_audio,
    'print': prints_correct.correct_print,
    'slide': slides_correct.correct_slide,
    'vhs': vhs_correct.correct_vhs
}

# API endpoint for updating task status
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')
UPDATE_TASK_ENDPOINT = f"{API_BASE_URL}/corr/tasks/"

def update_task_status(task_id, status, result=None, error_message=None):
    """
    Update the task status in the Django API
    """
    url = f"{UPDATE_TASK_ENDPOINT}{task_id}/"
    data = {
        'status': status
    }
    
    if result is not None:
        data['result'] = json.dumps(result)
    
    if error_message is not None:
        data['error_message'] = error_message
    
    try:
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to update task status: {e}")
        return False

@app.task(bind=True)
def process_correction(self, task_id, media_type, file_path, to_folder, options):
    """
    Generic task to process any type of media correction
    """
    try:
        # Update task status to PROCESSING
        update_task_status(task_id, 'PROCESSING')
        
        # Get the appropriate correction function
        if media_type not in CORRECTION_FUNCTIONS:
            raise ValueError(f"Invalid media type: {media_type}")
            
        correction_func = CORRECTION_FUNCTIONS[media_type]
        
        # Perform the correction
        result = correction_func(file_path, to_folder, options)
        
        # Update task status to COMPLETED
        update_task_status(task_id, 'COMPLETED', result=result)
        
        return result
    except Exception as e:
        # Update task status to FAILED
        update_task_status(task_id, 'FAILED', error_message=str(e))
        raise

if __name__ == '__main__':
    app.start()
