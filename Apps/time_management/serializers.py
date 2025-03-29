from rest_framework import serializers
from .models import TimeCategory, TimeEntry, Timesheet, TimesheetEntry, WorkSchedule
from Apps.users.models import User
from Apps.project.models import Project

class TimeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeCategory
        fields = ['id', 'name', 'description', 'is_billable', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class TimeEntrySerializer(serializers.ModelSerializer):
    hours = serializers.FloatField(read_only=True)
    
    class Meta:
        model = TimeEntry
        fields = ['id', 'user', 'project', 'category', 'description', 'start_time', 'end_time', 
                 'hours', 'is_billable', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time'
                })
        return data

    def create(self, validated_data):
        # Calculate hours from start_time and end_time
        if validated_data.get('start_time') and validated_data.get('end_time'):
            duration = validated_data['end_time'] - validated_data['start_time']
            validated_data['hours'] = round(duration.total_seconds() / 3600, 2)
        return super().create(validated_data)

class TimesheetSerializer(serializers.ModelSerializer):
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Timesheet
        fields = ['id', 'user', 'start_date', 'end_date', 'status', 'total_hours', 
                 'notes', 'submitted_at', 'approved_at', 'created_at', 'updated_at']
        read_only_fields = ['total_hours', 'submitted_at', 'approved_at', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })
        return data

class TimesheetEntrySerializer(serializers.ModelSerializer):
    hours = serializers.FloatField()
    category = serializers.PrimaryKeyRelatedField(queryset=TimeCategory.objects.all(), required=False)

    class Meta:
        model = TimesheetEntry
        fields = ['id', 'timesheet', 'time_entry', 'date', 'hours', 'category', 'description', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_hours(self, value):
        if value < 0:
            raise serializers.ValidationError("Hours cannot be negative")
        return value

    def create(self, validated_data):
        # Copy description from time_entry if not provided
        if 'description' not in validated_data and validated_data.get('time_entry'):
            validated_data['description'] = validated_data['time_entry'].description
        # Copy category from time_entry if not provided
        if 'category' not in validated_data and validated_data.get('time_entry'):
            validated_data['category'] = validated_data['time_entry'].category
        return super().create(validated_data)

class WorkScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSchedule
        fields = ['id', 'user', 'name', 'start_time', 'end_time', 'days_of_week', 'is_active', 
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time'
                })
        
        if data.get('days_of_week'):
            valid_days = list(range(0, 7))  # 0 = Monday, 6 = Sunday
            days = data['days_of_week']
            if not isinstance(days, list):
                days = [days]
            for day in days:
                if day not in valid_days:
                    raise serializers.ValidationError(f"Invalid day value: {day}. Must be between 0 and 6")
            data['days_of_week'] = days
        return data 