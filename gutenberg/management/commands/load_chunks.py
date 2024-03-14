from django.core.management.base import BaseCommand

from gutenberg.models import Chunk, Book

from django.db import connections


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        print("Loading chunks from bookbuilder.")
        with connections["bookbuilder"].cursor() as cursor:
            cursor.execute(
                'SELECT "gutenberg_chunk"."id", "gutenberg_chunk"."book_gutenberg_id", "gutenberg_chunk"."text", "gutenberg_chunk"."rel_i" FROM "gutenberg_chunk"'
            )
            bookbuilder_chunk_data = cursor.fetchall()

        print(f"{len(bookbuilder_chunk_data)} chunks found.")

        books = {}
        book_builder_ids = set()
        chunks = []
        created_count = 0
        for book_builder_id, book_gutenberg_id, text, rel_i in bookbuilder_chunk_data:
            book_builder_ids.add(book_builder_id)
            if book_gutenberg_id not in books:
                books[book_gutenberg_id] = Book.objects.get_or_create(
                    gutenberg_id=book_gutenberg_id
                )[0]

            chunks.append(
                Chunk(
                    book_builder_id=book_builder_id,
                    text=text,
                    rel_i=rel_i,
                    book_id=books[book_gutenberg_id].id,
                )
            )

            if len(chunks) >= 2500:
                Chunk.objects.bulk_create(chunks, batch_size=250, ignore_conflicts=True)
                created_count += len(chunks)
                print(f"{created_count} chunks scanned.")
                chunks = []

        Chunk.objects.bulk_create(chunks, batch_size=250, ignore_conflicts=True)
        created_count += len(chunks)
        print(f"{created_count} chunks created.")

        deleted_count = 0
        delete_ids = []
        for book_builder_id in Chunk.objects.values_list("book_builder_id", flat=True):
            if book_builder_id not in book_builder_ids:
                delete_ids.append(book_builder_id)
                if len(delete_ids) >= 250:
                    count, _ = Chunk.objects.filter(id__in=delete_ids).delete()
                    deleted_count += count
                    delete_ids = []

        count, _ = Chunk.objects.filter(id__in=delete_ids).delete()
        deleted_count += count

        print(f"{deleted_count} chunks deleted.")
