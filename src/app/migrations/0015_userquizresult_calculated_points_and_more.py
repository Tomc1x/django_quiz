# Generated by Django 5.1.7 on 2025-04-17 13:32

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_quiz_level'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='userquizresult',
            name='calculated_points',
            field=models.FloatField(default=0),
        ),
        migrations.AddIndex(
            model_name='userquizresult',
            index=models.Index(fields=['user', 'quiz'], name='app_userqui_user_id_453aa7_idx'),
        ),
        migrations.AddIndex(
            model_name='userquizresult',
            index=models.Index(fields=['-calculated_points'], name='app_userqui_calcula_e58bee_idx'),
        ),
    ]
