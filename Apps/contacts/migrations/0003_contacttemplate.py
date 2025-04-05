# Generated by Django 5.1.7 on 2025-04-05 17:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0002_initial'),
        ('entity', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('fields', models.JSONField(help_text='JSON structure defining the template fields and their properties')),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contact_templates_created', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contact_templates', to='entity.organization')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contact_templates_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Contact Template',
                'verbose_name_plural': 'Contact Templates',
                'ordering': ['name'],
                'unique_together': {('name', 'organization')},
            },
        ),
    ]
