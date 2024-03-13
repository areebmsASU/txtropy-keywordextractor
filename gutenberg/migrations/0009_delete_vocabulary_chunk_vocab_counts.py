# Generated by Django 5.0.2 on 2024-03-06 23:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gutenberg', '0008_chunk_lemma_counts'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Vocabulary',
        ),
        migrations.AddField(
            model_name='chunk',
            name='vocab_counts',
            field=models.JSONField(null=True),
        ),
    ]
