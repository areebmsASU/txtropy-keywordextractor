from django.db import models


class Chunk(models.Model):
    book_builder_id = models.IntegerField(unique=True)
    book_gutenberg_id = models.IntegerField()
    text = models.TextField()
    token_counts = models.JSONField(null=True)
    lemma_counts = models.JSONField(null=True)
    vocab_counts = models.JSONField(null=True)
    rel_i = models.IntegerField()


class Book(models.Model):
    gutenberg_id = models.IntegerField(unique=True)
    text_lemma_counts = models.JSONField(null=True)


class Lemma(models.Model):
    text = models.TextField(unique=True, db_index=True)

    def __str__(self) -> str:
        return self.text


class Word(models.Model):
    text = models.TextField(db_index=True, unique=True)
    lemma = models.ForeignKey(Lemma, on_delete=models.CASCADE, related_name="words")

    def __str__(self) -> str:
        return self.text

    class Meta:
        unique_together = [
            ["text", "lemma"],
        ]
