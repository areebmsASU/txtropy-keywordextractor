from django.db import models


class Book(models.Model):
    gutenberg_id = models.IntegerField(unique=True)
    title = models.TextField()
    author = models.TextField()

    text_lemma_counts = models.JSONField(null=True)

    def status(self):
        return self.chunks.aggregate(
            chunk_count=models.Count("pk"),
            chunk_has_token=models.Count("pk", filter=~models.Q(token_counts=None)),
            chunk_has_lemma=models.Count("pk", filter=~models.Q(lemma_counts=None)),
            chunk_has_vocab=models.Count("pk", filter=~models.Q(vocab_counts=None)),
        )


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
    stem = models.TextField(null=True)

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
