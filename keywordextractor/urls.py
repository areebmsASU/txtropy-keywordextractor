from django.urls import path
from gutenberg.views import books, create_chunk, lemma, words

urlpatterns = [
    path("books/", books),
    path("chunk/", create_chunk),
    path("lemma/<slug:lemma>/", words),
    path("lemma/", lemma),
]
