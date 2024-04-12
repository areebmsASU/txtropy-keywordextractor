from django.urls import path
from gutenberg.views import create_book, create_chunk, main, lemma, words

urlpatterns = [
    path("", main),
    path("book/", create_book),
    path("chunk/", create_chunk),
    path("lemma/<slug:lemma>/", words),
    path("lemma/", lemma),
]
