# Generated by Django 5.0.2 on 2024-03-06 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gutenberg', '0007_rename_tokens_chunk_token_counts'),
    ]

    operations = [
        migrations.AddField(
            model_name='chunk',
            name='lemma_counts',
            field=models.JSONField(null=True),
        ),
    ]
