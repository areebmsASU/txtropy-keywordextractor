from celery import shared_task

from gutenberg.models import Book
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
            created = Book.objects.get_or_create(
                gutenberg_id=request.POST["id"],
                subject_gutenberg_id=request.POST["subject_id"],
                title=request.POST["title"],
                author=request.POST["author"],
            )[1]
        except Exception as e:
            return JsonResponse({"error": e.args[0]}, status_code=400)
    return JsonResponse({"created": created})


def create_chunk(request):
    if request.method == "POST":
        try:
            book = Book.objects.filter(gutenberg_id=request.POST["book_id"]).first()
            if book is None:
                return JsonResponse({"error": "Book not found."}, status_code=404)

            created = book.chunks.get_or_create(
                book_builder_id=request.POST["id"], text=request.POST["text"]
            )[1]
        except Exception as e:
            return JsonResponse({"error": e.args[0]}, status_code=400)
    return JsonResponse({"created": created})
