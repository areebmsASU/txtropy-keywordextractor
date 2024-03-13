from django.core.management.base import BaseCommand

from gutenberg.models import Chunk, Book

from django.db import connections


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        # Chunk.objects.all().delete()
        book_gutenberg_ids = set()
        with connections["bookbuilder"].cursor() as cursor:
            cursor.execute(
                'SELECT "gutenberg_chunk"."id", "gutenberg_chunk"."book_gutenberg_id", "gutenberg_chunk"."text", "gutenberg_chunk"."rel_i" FROM "gutenberg_chunk"'
            )
            bookbuilder_chunk_data = cursor.fetchall()

        for book_builder_id, book_gutenberg_id, text, rel_i in bookbuilder_chunk_data:
            book_gutenberg_ids.add(book_gutenberg_id)
            Chunk.objects.create(
                book_builder_id=book_builder_id,
                book_gutenberg_id=book_gutenberg_id,
                text=text,
                rel_i=rel_i,
            )

        for book_gutenberg_id in book_gutenberg_ids:
            Book.objects.get_or_create(gutenberg_id=book_gutenberg_id)
