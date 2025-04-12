from rest_framework import serializers

class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audit
        fields = ['id', 'action', 'user', 'resource', 'details', 'timestamp', 'organization', 'retention_period']
        read_only_fields = ['id', 'timestamp', 'organization']

    def validate(self, data):
        """
        Validate the audit data.
        """
        if not data.get('action'):
            raise serializers.ValidationError("Action is required.")
        if not data.get('user'):
            raise serializers.ValidationError("User is required.")
        return data 