import pytest
from django.core.exceptions import ValidationError
from ..models import Organization, OrganizationSettings

@pytest.mark.django_db
class TestOrganizationSettings:
    def test_create_organization_settings(self):
        """Test creating organization settings"""
        org = Organization.objects.create(name="Test Org")
        settings = OrganizationSettings.objects.create(
            organization=org,
            timezone="UTC",
            date_format="YYYY-MM-DD",
            time_format="24h",
            language="en",
            notification_preferences={
                "email": True,
                "push": True,
                "slack": False
            }
        )
        assert settings.organization == org
        assert settings.timezone == "UTC"
        assert settings.date_format == "YYYY-MM-DD"
        assert settings.time_format == "24h"
        assert settings.language == "en"
        assert settings.notification_preferences["email"] is True

    def test_organization_settings_unique_constraint(self):
        """Test that an organization can only have one settings object"""
        org = Organization.objects.create(name="Test Org")
        OrganizationSettings.objects.create(
            organization=org,
            notification_preferences={"email": True, "push": True, "slack": False}
        )
        
        with pytest.raises(ValidationError):
            OrganizationSettings.objects.create(
                organization=org,
                notification_preferences={"email": True, "push": True, "slack": False}
            )

    def test_organization_settings_default_values(self):
        """Test default values for organization settings"""
        org = Organization.objects.create(name="Test Org")
        settings = OrganizationSettings.objects.create(
            organization=org,
            notification_preferences={"email": True, "push": True, "slack": False}
        )
        
        assert settings.timezone == "UTC"
        assert settings.date_format == "YYYY-MM-DD"
        assert settings.time_format == "24h"
        assert settings.language == "en"
        assert settings.notification_preferences == {
            "email": True,
            "push": True,
            "slack": False
        }

    def test_organization_settings_validation(self):
        """Test validation of organization settings"""
        org = Organization.objects.create(name="Test Org")
        
        # Test invalid timezone
        with pytest.raises(ValidationError):
            OrganizationSettings.objects.create(
                organization=org,
                timezone="Invalid/Timezone"
            )
        
        # Test invalid date format
        with pytest.raises(ValidationError):
            OrganizationSettings.objects.create(
                organization=org,
                date_format="Invalid Format"
            )
        
        # Test invalid time format
        with pytest.raises(ValidationError):
            OrganizationSettings.objects.create(
                organization=org,
                time_format="Invalid Format"
            )
        
        # Test invalid language
        with pytest.raises(ValidationError):
            OrganizationSettings.objects.create(
                organization=org,
                language="invalid"
            )

    def test_organization_settings_update(self):
        """Test updating organization settings"""
        org = Organization.objects.create(name="Test Org")
        settings = OrganizationSettings.objects.create(
            organization=org,
            notification_preferences={"email": True, "push": True, "slack": False}
        )
        
        settings.timezone = "America/New_York"
        settings.date_format = "MM/DD/YYYY"
        settings.time_format = "12h"
        settings.language = "es"
        settings.notification_preferences = {
            "email": False,
            "push": True,
            "slack": True
        }
        settings.save()
        
        updated_settings = OrganizationSettings.objects.get(organization=org)
        assert updated_settings.timezone == "America/New_York"
        assert updated_settings.date_format == "MM/DD/YYYY"
        assert updated_settings.time_format == "12h"
        assert updated_settings.language == "es"
        assert updated_settings.notification_preferences["email"] is False 