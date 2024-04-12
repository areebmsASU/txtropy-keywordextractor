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


def create_book(request):
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
