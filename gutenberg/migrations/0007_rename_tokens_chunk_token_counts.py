# Generated by Django 5.0.2 on 2024-03-04 18:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gutenberg', '0006_chunk_tokens'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chunk',
            old_name='tokens',
            new_name='token_counts',
        ),
    ]
