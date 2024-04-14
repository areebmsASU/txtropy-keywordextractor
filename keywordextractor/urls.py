from django.urls import path
from gutenberg.views import books, create_chunk, main, lemma, words

urlpatterns = [
    path("", main),
    path("books/", books),
    path("chunk/", create_chunk),
    path("lemma/<slug:lemma>/", words),
    path("lemma/", lemma),
]
