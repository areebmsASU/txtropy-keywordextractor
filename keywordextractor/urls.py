from django.urls import path
from gutenberg.views import books, create_chunk, lemma, words, count_tokens, count_lemmas

urlpatterns = [
    path("books/", books),
    path("chunk/", create_chunk),
    path("lemma/<slug:lemma>/", words),
    path("lemma/", lemma),
    path("count_tokens/", count_tokens),
    path("count_lemmas/", count_lemmas),
]
