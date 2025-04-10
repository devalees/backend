# Generated by Django 4.2.11 on 2025-04-10 06:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('communication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_threads', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='thread',
            name='participants',
            field=models.ManyToManyField(related_name='threads', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='richtextmessage',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='richtextmessage',
            name='thread',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='communication.thread'),
        ),
        migrations.AddField(
            model_name='notification',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='thread',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='communication.thread'),
        ),
        migrations.AddIndex(
            model_name='translation',
            index=models.Index(fields=['source_text', 'target_language'], name='communicati_source__59abfb_idx'),
        ),
        migrations.AddIndex(
            model_name='translation',
            index=models.Index(fields=['created_at'], name='communicati_created_064c19_idx'),
        ),
    ]
