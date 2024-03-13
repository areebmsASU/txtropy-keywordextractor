# Generated by Django 5.0.2 on 2024-03-04 03:28

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gutenberg', '0002_chunk_book_builder_id_alter_chunk_rel_i'),
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gutenberg_id', models.IntegerField()),
                ('text_lemma_counts', models.JSONField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Lemma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(db_index=True, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Vocabulary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('words', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), size=None)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(db_index=True)),
                ('lemma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='words', to='gutenberg.lemma')),
            ],
            options={
                'unique_together': {('text', 'lemma')},
            },
        ),
    ]
