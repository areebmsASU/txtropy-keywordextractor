from collections import Counter
from time import sleep

from concurrent.futures import ThreadPoolExecutor, wait
from django.core.management.base import BaseCommand
from nltk.stem.snowball import SnowballStemmer

from gutenberg.models import Book, Chunk, Word


class ChunkLemmatizer:
    def __init__(self, chunk_qs, batch_size=100) -> None:
        self.executor = ThreadPoolExecutor()
        self.executor_futures = []
        self.chunk_qs = chunk_qs
        self.batch_size = batch_size
        self.stemmer = SnowballStemmer(language="english")
        self.vocabulary = []

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

        Chunk.objects.bulk_update(chunks, fields=["vocab_counts"], batch_size=self.batch_size)

    def print_execution_status(self):
        done, not_done = wait(self.executor_futures, return_when="FIRST_COMPLETED")
        while len(not_done):
            sleep(5)
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
            for gutenberg_id in Book.objects.values_list("gutenberg_id", flat=True).distinct():
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
        chunk_qs = Chunk.objects.filter(token_counts__isnull=False).order_by("id")
        lemmatizer = ChunkLemmatizer(chunk_qs=chunk_qs)
        lemmatizer.start()

        # chunks = []
        # print(Chunk.objects.exclude(vocab_counts__isnull=True).count())
        # for chunk in Chunk.objects.exclude(vocab_counts__isnull=True):
        #    chunk.vocab_counts = chunk.lemma_counts
        #    chunks.append(chunk)
        # Chunk.objects.bulk_update(chunks, ["vocab_counts"], 250)
