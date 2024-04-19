from django.urls import path
from gutenberg.views import (
    books,
    create_chunk,
    lemma,
    words,
    count_tokens,
    count_lemmas,
    bulk_count_tokens,
    bulk_count_lemmas,
    status,
)

urlpatterns = [
    path("books/", books),
    path("chunk/", create_chunk),
    path("lemma/<slug:lemma>/", words),
    path("lemma/", lemma),
    path("count_tokens/", count_tokens),
    path("count_lemmas/", count_lemmas),
    path("bulk_count_tokens/", bulk_count_tokens),
    path("bulk_count_lemmas/", bulk_count_lemmas),
    path("status/", status),
]
