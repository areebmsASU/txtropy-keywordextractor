from collections import Counter, defaultdict
from time import sleep

from concurrent.futures import ThreadPoolExecutor, wait
from django.core.management.base import BaseCommand
from nltk.stem.snowball import SnowballStemmer

from gutenberg.models import Book, Chunk, Word


class ChunkLemmatizer:
    def __init__(self, chunk_qs, batch_size=100) -> None:
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor_futures = []
        self.chunk_qs = chunk_qs
        self.batch_size = batch_size
        self.stemmer = SnowballStemmer(language="english")
        self.vocabulary = []

    def lemmatize(self, chunk_ids):
        lemmas = {
            word: _lemma
            for word, _lemma in Word.objects.values_list("text", "lemma__text")
        }

        chunks = []
        for chunk in Chunk.objects.filter(id__in=chunk_ids).only("token_counts"):
            chunk.lemma_counts = defaultdict(int)
            for token, count in chunk.token_counts.items():
                if token in lemmas:
                    stem = self.stemmer.stem(lemmas[token])
                    if len(stem) > 2:
                        chunk.lemma_counts[stem] += count

            chunk.lemma_counts = dict(chunk.lemma_counts)
            if chunk.lemma_counts:
                chunks.append(chunk)

        Chunk.objects.bulk_update(
            chunks, fields=["lemma_counts"], batch_size=self.batch_size
        )

    def count_book_lemma(self, gutenberg_id):
        book = Book.objects.get(gutenberg_id=gutenberg_id)
        book.text_lemma_counts = dict(
            sum(
                map(
                    lambda counts: Counter(**counts),
                    list(
                        Chunk.objects.filter(
                            book_gutenberg_id=gutenberg_id, lemma_counts__isnull=False
                        ).values_list("lemma_counts", flat=True)
                    ),
                ),
                Counter(),
            )
        )
        book.save(update_fields=["text_lemma_counts"])

    def update_vocab(self, chunk_ids):
        if not self.vocabulary:
            self.load_vocabulary()

        chunks = []
        for chunk in Chunk.objects.filter(id__in=chunk_ids).only("lemma_counts"):
            chunk.vocab_counts = {
                token: count
                for token, count in chunk.lemma_counts.items()
                if token in self.vocabulary
            }

            chunks.append(chunk)

        Chunk.objects.bulk_update(
            chunks, fields=["vocab_counts"], batch_size=self.batch_size
        )

    def print_execution_status(self):
        done, not_done = wait(self.executor_futures, return_when="FIRST_COMPLETED")
        while len(not_done):
            sleep(3)
            done, not_done = wait(self.executor_futures, return_when="FIRST_COMPLETED")
            print(
                f"{len(not_done)} of {(len(done) + len(not_done))} tasks ({int((100 * len(not_done)) / (len(done) + len(not_done)))}%) remaining."
            )
        self.executor_futures = []

    def load_vocabulary(self, min_books=5):
        self.vocabulary = [
            lemma
            for lemma, count in Counter(
                sum(
                    list(
                        map(
                            list,
                            Book.objects.values_list("text_lemma_counts", flat=True),
                        )
                    ),
                    [],
                )
            ).items()
            if count >= min_books
        ]

    def start(self, lemmatize=True, get_vocab=True, populate_vocab=True):
        chunk_ids = list(self.chunk_qs.values_list("id", flat=True))
        print(f"Found {len(chunk_ids)} chunks.")
        if lemmatize:
            print("Lemmatizing")
            for i in range(0, len(chunk_ids), self.batch_size):
                self.executor_futures.append(
                    self.executor.submit(
                        self.lemmatize, chunk_ids=chunk_ids[i : i + self.batch_size]
                    )
                )
            self.print_execution_status()

        if get_vocab:
            print(f"Determining Vocabulary")
            for gutenberg_id in set(
                self.chunk_qs.values_list("book_gutenberg_id", flat=True).distinct()
            ):
                self.executor_futures.append(
                    self.executor.submit(self.count_book_lemma, gutenberg_id)
                )
            self.print_execution_status()

        if populate_vocab:
            print(f"Populating chunk vocabulary")
            self.load_vocabulary()
            for i in range(0, len(chunk_ids), self.batch_size):
                self.executor_futures.append(
                    self.executor.submit(
                        self.update_vocab, chunk_ids=chunk_ids[i : i + self.batch_size]
                    )
                )
            self.print_execution_status()


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        chunk_qs = (
            Chunk.objects.filter(token_counts__isnull=False)
            .filter(vocab_counts__isnull=True)
            .order_by("id")
        )
        lemmatizer = ChunkLemmatizer(chunk_qs=chunk_qs)
        lemmatizer.start()
