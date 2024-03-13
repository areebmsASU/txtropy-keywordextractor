from django.core.management.base import BaseCommand

from gutenberg.models import Chunk, Book

from django.db import connections


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        # Chunk.objects.all().delete()

        with connections["bookbuilder"].cursor() as cursor:
            cursor.execute(
                'SELECT "gutenberg_chunk"."id", "gutenberg_chunk"."book_gutenberg_id", "gutenberg_chunk"."text", "gutenberg_chunk"."rel_i" FROM "gutenberg_chunk"'
            )
            bookbuilder_chunk_data = cursor.fetchall()

        books = {}
        book_builder_ids = set()
        for book_builder_id, book_gutenberg_id, text, rel_i in bookbuilder_chunk_data:
            book_builder_ids.add(book_builder_id)
            if book_gutenberg_id not in books:
                books[book_gutenberg_id] = Book.objects.get_or_create(
                    gutenberg_id=book_gutenberg_id
                )[0]

            books[book_gutenberg_id].chunks.get_or_create(
                book_builder_id=book_builder_id, text=text, rel_i=rel_i
            )

        for chunk in Chunk.objects.all().only("book_builder_id"):
            if chunk.book_builder_id not in book_builder_ids:
                chunk.delete()
