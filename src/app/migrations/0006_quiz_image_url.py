# Generated by Django 5.1.7 on 2025-03-26 00:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_alter_userquizresult_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='image_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
