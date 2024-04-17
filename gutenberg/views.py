from collections import defaultdict

import requests
from celery import shared_task
from django.db.models import Count, Q
from django.http import JsonResponse

from gutenberg.models import Book, Lemma, Chunk
from gutenberg.tokenize import get_token_count


BOOKBUILDER_URL = "http://api.bookbuilder.txtropy.com"


@shared_task
def load_chunks(gutenberg_id):

    book = Book.objects.get(gutenberg_id=gutenberg_id)

    data = requests.get(f"{BOOKBUILDER_URL}/chunks/{gutenberg_id}/").json()

    created_ids = []
    while data["chunks"]:
        chunks = []
        for chunk in data["chunks"]:
            chunks.append(Chunk(book_builder_id=chunk["id"], text=chunk["text"], book_id=book.id))
            created_ids.append(chunk["id"])
        Chunk.objects.bulk_create(chunks)
        if "next_page" in data:
            data = requests.get(data["next_page"]).json()
        else:
            break

    book.chunks.exclude(book_builder_id__in=created_ids).delete()


def books(request):
    if request.method == "POST":
        try:
            book = Book.objects.filter(gutenberg_id=request.POST["id"]).first()
            if book is None:
                Book.objects.create(
                    gutenberg_id=request.POST["id"],
                    title=request.POST["title"],
                    author=request.POST["author"],
                )[1]
                status = "created"
            elif book.title == request.POST["title"] and book.author == request.POST["author"]:
                status = "ignored"
            else:
                book.title = request.POST["title"]
                book.author = request.POST["author"]
                book.save(update_fields=["title", "author"])
                status = "updated"

        except Exception as e:

            return JsonResponse({"error": repr(e)}, status=400)
        load_chunks.delay(gutenberg_id=book.gutenberg_id)
        return JsonResponse({"status": status})
    elif request.method == "GET":
        counts = defaultdict(dict)
        for gutenberg_id, chunk_count, token_count in (
            Book.objects.annotate(chunk_count=Count("chunks"))
            .annotate(token_count=Count("chunks", filter=~Q(chunks__token_counts=None)))
            .values_list("gutenberg_id", "chunk_count", "token_count")
        ):
            counts[gutenberg_id]["total"] = chunk_count
            counts[gutenberg_id]["tokens"] = token_count
        return JsonResponse(counts)
    elif request.method == "DELETE":
        try:
            book = Book.objects.filter(gutenberg_id=request.POST["book_id"]).first()
            if book is None:
                return JsonResponse({"error": "Book not found."}, status=404)

            res = book.chunks.all().delete()
        except Exception as e:
            return JsonResponse({"error": repr(e)}, status=400)
        return JsonResponse({"created": res})


def count_tokens(request):
    if request.method == "POST":
        task_id = get_token_count(gutenberg_id=request.POST["book_id"])
        return JsonResponse({"task": task_id})


def create_chunk(request):
    if request.method == "POST":
        try:
            book = Book.objects.filter(gutenberg_id=request.POST["book_id"]).first()
            if book is None:
                return JsonResponse({"error": "Book not found."}, status=404)

            created = book.chunks.get_or_create(
                book_builder_id=request.POST["id"], text=request.POST["text"]
            )[1]
        except Exception as e:
            return JsonResponse({"error": repr(e)}, status=400)
    return JsonResponse({"created": created})


def lemma(request):
    return JsonResponse(
        list(
            Lemma.objects.annotate(count=Count("words")).values("text", "count").order_by("-count")
        ),
        safe=False,
    )


def words(request, lemma):
    lemma = Lemma.objects.get(text=lemma)
    return JsonResponse(list(lemma.words.values("text")), safe=False)
