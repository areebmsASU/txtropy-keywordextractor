from django.urls import path
from gutenberg.views import create_book, create_chunk, main

urlpatterns = [
    path("", main),
    path("book/", create_book),
    path("chunk/", create_chunk),
]
