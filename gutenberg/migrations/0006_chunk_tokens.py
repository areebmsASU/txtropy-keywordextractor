# Generated by Django 5.0.2 on 2024-03-04 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gutenberg', '0005_alter_word_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='chunk',
            name='tokens',
            field=models.JSONField(null=True),
        ),
    ]
