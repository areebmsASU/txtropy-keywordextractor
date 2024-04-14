from celery import shared_task
from django.db.models import Count

from gutenberg.models import Book, Lemma
from django.http import JsonResponse


@shared_task
def test():
    print("Tested.")


def main(request):
    test.delay()
    return JsonResponse({})


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
        return JsonResponse({"status": status})
    elif request.method == "GET":
        counts = {}
        for gutenberg_id, chunk_count in Book.objects.annotate(
            chunk_count=Count("chunks")
        ).values_list("gutenberg_id", "chunk_count"):
            counts[gutenberg_id] = chunk_count
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


def create_chunk(request):
    if request.method == "POST":
        try:
            book = Book.objects.filter(gutenberg_id=request.POST["book_id"]).first()
            if book is None:
                return JsonResponse({"error": "Book not found."}, status=404)

            delete = book.chunks.get_or_create(
                book_builder_id=request.POST["id"], text=request.POST["text"]
            )[1]
        except Exception as e:
            return JsonResponse({"error": repr(e)}, status=400)
    return JsonResponse({"delete": delete})


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
