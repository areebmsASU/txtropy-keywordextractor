from django.db import models


class Book(models.Model):
    gutenberg_id = models.IntegerField(unique=True)
    title = models.TextField()
    author = models.TextField()

    text_lemma_counts = models.JSONField(null=True)


class Chunk(models.Model):
    book_builder_id = models.IntegerField(unique=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chunks")
    text = models.TextField()

    token_counts = models.JSONField(null=True)
    lemma_counts = models.JSONField(null=True)
    vocab_counts = models.JSONField(null=True)

    last_modified = models.DateTimeField(auto_now=True)


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
