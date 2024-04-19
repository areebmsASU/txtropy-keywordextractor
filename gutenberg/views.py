import json
from collections import defaultdict, Counter

import requests
from celery import shared_task
from django.db.models import Count, Q
from django.http import JsonResponse

from gutenberg.models import Book, Lemma, Chunk
from gutenberg.pipeline_tasks import (
    async_count_tokens,
    async_count_lemmas,
    async_bulk_count_lemmas,
    async_bulk_count_tokens,
)


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


def status(request):
    books = 0
    tokenized = 0
    lemmatized = 0
    filtered = 0
    details = []
    for book in Book.objects.all():
        books += 1
        status = book.status()
        chunk_count = status.pop("chunk_count")
        tokenized += int(chunk_count == status["chunk_has_token"])
        lemmatized += int(chunk_count == status["chunk_has_lemma"])
        filtered += int(chunk_count == status["chunk_has_vocab"])

        details.append(
            {
                "id": book.gutenberg_id,
                "chunk_count": chunk_count,
                **{
                    k: round(v / chunk_count, 2) if chunk_count else "N/A"
                    for k, v in status.items()
                },
            }
        )

    return JsonResponse(
        {
            "summary": {
                "books": books,
                "tokenized": tokenized,
                "lemmatized": lemmatized,
                "filtered": filtered,
            },
            "details": details,
        }
    )


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
        for gutenberg_id, chunk_count, token_count, text_lemma_counts in (
            Book.objects.annotate(chunk_count=Count("chunks"))
            .annotate(token_count=Count("chunks", filter=~Q(chunks__token_counts=None)))
            .values_list("gutenberg_id", "chunk_count", "token_count", "text_lemma_counts")
        ):
            counts[gutenberg_id]["total"] = chunk_count
            counts[gutenberg_id]["tokens"] = token_count
            counts[gutenberg_id]["lemma_counts"] = bool(text_lemma_counts)
        return JsonResponse(dict(counts))
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
        body_data = json.loads(request.body.decode("utf-8"))
        task_id = async_count_tokens.delay(gutenberg_id=body_data["book_id"]).task_id
        return JsonResponse({"task": task_id})


def bulk_count_tokens(request):
    if request.method == "POST":
        task_id = async_bulk_count_tokens.delay().task_id
        return JsonResponse({"task": task_id})


def count_lemmas(request):
    if request.method == "POST":
        body_data = json.loads(request.body.decode("utf-8"))
        task_id = async_count_lemmas.delay(gutenberg_id=body_data["book_id"]).task_id
        return JsonResponse({"task": task_id})


def bulk_count_lemmas(request):
    if request.method == "POST":
        task_id = async_bulk_count_lemmas.delay().task_id
        return JsonResponse({"task": task_id})


def words(request, lemma):
    return JsonResponse(list(Lemma.objects.get(text=lemma).words.values("text")), safe=False)


def lemma(request):

    words = Counter()
    for lemma_text, word_count in Lemma.objects.annotate(count=Count("words")).values_list(
        "stem", "count"
    ):
        words.update({lemma_text: word_count})
    words = dict(words)

    return JsonResponse(
        [
            {"lemma": lemma, "instances": instances, "words": words.get(lemma)}
            for lemma, instances in sum(
                [
                    Counter(text_lemma_counts)
                    for text_lemma_counts in Book.objects.values_list(
                        "text_lemma_counts", flat=True
                    )
                ],
                Counter(),
            ).most_common()
        ],
        safe=False,
    )


def chunks(request, gutenberg_id):
    i = request.GET.get("i", 0)

    book = Book.objects.filter(gutenberg_id=gutenberg_id).first()
    if book is None:
        return JsonResponse({"error": "Book not found."}, status=404)

    data = {
        "chunks": [
            {
                "id": chunk_data["book_builder_id"],
                "text": chunk_data["text"],
                "vocab_counts": chunk_data["vocab_counts"],
                "last_modified": chunk_data["last_modified"],
            }
            for chunk_data in book.chunks.filter(book_builder_id__gte=i)
            .order_by("book_builder_id")[:251]
            .values("book_builder_id", "text", "vocab_counts", "last_modified")
        ]
    }

    if len(data["chunks"]) > 250:
        base_url = request.build_absolute_uri().split("?")[0]
        next_chunk_id = data["chunks"].pop()["id"]
        data["next_page"] = f"{base_url}?i={next_chunk_id}"

    return JsonResponse(data)
