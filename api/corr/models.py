from django.db import models
import json

class CorrectionTask(models.Model):
    TASK_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    MEDIA_TYPE_CHOICES = [
        ('slide', 'Slide'),
        ('print', 'Print'),
        ('audio', 'Audio'),
        ('vhs', 'VHS'),
    ]
    
    task_id = models.CharField(max_length=255, unique=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file_path = models.CharField(max_length=1024)
    to_folder = models.CharField(max_length=1024)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='PENDING')
    result = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    options = models.TextField(default='{}')  # JSON serialized options
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.media_type} - {self.task_id} - {self.status}"
    
    def set_options(self, options_dict):
        self.options = json.dumps(options_dict)
    
    def get_options(self):
        return json.loads(self.options)
