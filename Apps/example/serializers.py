from rest_framework import serializers
from .models import ExampleModel

class ExampleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleModel
        fields = ['id', 'name', 'data', 'task_status', 'task_id', 
                 'error_message', 'processed_at', 'task_result']
        read_only_fields = ['task_status', 'task_id', 'error_message', 
                          'processed_at', 'task_result'] 