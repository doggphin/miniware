from celery import shared_task
import os
import uuid
from .models import CorrectionTask
from .audio import audio_correct
from .prints import prints_correct
from .slides import slides_correct
from .video import vhs_correct

# Dictionary mapping media types to their correction functions
CORRECTION_FUNCTIONS = {
    'audio': audio_correct.correct_audio,
    'print': prints_correct.correct_print,
    'slide': slides_correct.correct_slide,
    'vhs': vhs_correct.correct_vhs
}

@shared_task(bind=True)
def process_correction(self, task_id, media_type, file_path, to_folder, options):
    """
    Generic task to process any type of media correction
    """
    try:
        # Update task status to PROCESSING
        task = CorrectionTask.objects.get(task_id=task_id)
        task.status = 'PROCESSING'
        task.save()
        
        # Get the appropriate correction function
        if media_type not in CORRECTION_FUNCTIONS:
            raise ValueError(f"Invalid media type: {media_type}")
            
        correction_func = CORRECTION_FUNCTIONS[media_type]
        
        # Perform the correction
        result = correction_func(file_path, to_folder, options)
        
        # Update task status to COMPLETED
        task.status = 'COMPLETED'
        task.result = str(result)
        task.save()
        
        return result
    except Exception as e:
        # Update task status to FAILED
        task = CorrectionTask.objects.get(task_id=task_id)
        task.status = 'FAILED'
        task.error_message = str(e)
        task.save()
        raise

def create_correction_task(media_type, file_path, to_folder, options):
    """
    Create a correction task and return the task ID
    """
    if media_type not in CORRECTION_FUNCTIONS:
        raise ValueError(f"Invalid media type: {media_type}")
        
    task_id = str(uuid.uuid4())
    
    # Create task record
    task = CorrectionTask(
        task_id=task_id,
        media_type=media_type,
        file_path=file_path,
        to_folder=to_folder,
        status='PENDING'
    )
    task.set_options(options)
    task.save()
    
    # Dispatch task to worker
    process_correction.delay(task_id, media_type, file_path, to_folder, options)
    
    return task_id
