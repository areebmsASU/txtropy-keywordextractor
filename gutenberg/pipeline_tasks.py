from collections import Counter

import spacy
import requests as r
from celery import shared_task
from concurrent.futures import ThreadPoolExecutor, wait
from django.db import transaction
from unidecode import unidecode
from nltk.stem.snowball import SnowballStemmer

from gutenberg.models import Chunk, Lemma, Word, Book

RELENTROPYGETTER_URL = "https://api.relentropygetter.txtropy.com"


class LemmaSyncer:
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor()
        self.stemmer = SnowballStemmer(language="english")
        self.executor_futures = []
        self.word_by_lemma = {}

    @staticmethod
    def replace_lemma(old_lemma_obj, new_lemma_obj):
        old_lemma_obj.words.update(lemma=new_lemma_obj)
        assert old_lemma_obj.words.all().count() == 0
        old_lemma_obj.delete()
        return new_lemma_obj

    @staticmethod
    def sort_lemma(this, other):
        # to_keep, to_drop
        if len(this.text) < len(other.text):
            return this, other
        if len(this.text) > len(other.text):
            return other, this
        if this.words.count() > other.words.count():
            return this, other
        if this.words.count() < other.words.count():
            return other, this

        return sorted([other, this], key=lambda l: l.text)

    def get_or_create_lemma(self, lemma):
        changed = False
        lemma_obj = Lemma.objects.filter(text=lemma).first()
        word_obj = Word.objects.filter(text=lemma).first()

        if lemma_obj and word_obj:
            if word_obj.lemma.id != lemma_obj.id:
                if (len(word_obj.lemma.text) < len(lemma_obj.text)) or (
                    word_obj.lemma.words.count() > lemma_obj.words.count()
                ):
                    changed = True
                    lemma_obj = self.replace_lemma(
                        old_lemma_obj=lemma_obj, new_lemma_obj=word_obj.lemma
                    )
                else:
                    raise Exception
        elif lemma_obj and not word_obj:
            changed = True
            lemma_obj.words.create(text=lemma)
        elif not lemma_obj and word_obj:
            if len(lemma) < len(word_obj.lemma.text):
                changed = True
                lemma_obj = self.replace_lemma(
                    new_lemma_obj=Lemma.objects.create(text=lemma, stem=self.stemmer(lemma)),
                    old_lemma_obj=word_obj.lemma,
                )
            else:
                lemma_obj = word_obj.lemma

        elif not lemma_obj and not word_obj:
            changed = True
            lemma_obj = Lemma.objects.create(text=lemma, stem=self.stemmer(lemma))
            lemma_obj.words.create(text=lemma)
        return lemma_obj, changed

    def add(self, lemma, word):
        self.executor_futures.append(self.executor.submit(self._add, lemma, word))

    def print_execution_status(self):
        done, not_done = wait(self.executor_futures, return_when="FIRST_COMPLETED")
        while len(not_done):
            print(
                f"{len(not_done)} of {(len(done) + len(not_done))} tasks ({int((100 * len(not_done)) / (len(done) + len(not_done)))}%) remaining."
            )
            done, not_done = wait(self.executor_futures, return_when="FIRST_COMPLETED")

        self.executor_futures = []

    def refresh_lemma_by_word(self):
        self.lemma_by_word = {
            word: lemma for word, lemma in Word.objects.values_list("text", "lemma__text")
        }

    def _add(self, lemma, word):
        if self.lemma_by_word.get("word") == lemma:
            return

        with transaction.atomic():
            lemma_obj, changed = self.get_or_create_lemma(lemma=lemma)
            word_obj = Word.objects.filter(text=word).first()

            if word_obj:
                if word_obj.lemma.id != lemma_obj.id:
                    new, old = self.sort_lemma(lemma_obj, word_obj.lemma)
                    lemma_obj = self.replace_lemma(old_lemma_obj=old, new_lemma_obj=new)
                    changed = True
            else:
                lemma_obj.words.create(text=word)
                changed = True

        if changed:
            self.refresh_lemma_by_word()


@shared_task
def async_count_tokens(gutenberg_id):
    book = Book.objects.get(gutenberg_id=gutenberg_id)
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    lemma_syncer = LemmaSyncer()

    chunks = []
    for chunk in book.chunks.order_by("id"):
        tokens = []
        for token in nlp(unidecode(chunk.text)):
            if token.is_alpha and not token.is_stop:
                # learn lemma for each token
                lemma_syncer.add(lemma=token.lemma_.lower(), word=token.lower_)
                tokens.append(token.lemma_.lower())
        chunk.token_counts = dict(Counter(tokens))  # save token
        chunks.append(chunk)

    Chunk.objects.bulk_update(chunks, ["token_counts"], batch_size=250)

    lemma_syncer.print_execution_status()


@shared_task
def async_bulk_count_tokens():
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    lemma_syncer = LemmaSyncer()
    for book in Book.objects.all():
        status = book.status()
        if status["chunk_has_token"] < status["chunk_count"]:
            chunks = []
            for chunk in book.chunks.filter(token_counts__isnull=True).order_by("id"):
                tokens = []
                for token in nlp(unidecode(chunk.text)):
                    if token.is_alpha and not token.is_stop:
                        # learn lemma for each token
                        lemma_syncer.add(lemma=token.lemma_.lower(), word=token.lower_)
                        tokens.append(token.lemma_.lower())
                chunk.token_counts = dict(Counter(tokens))  # save token
                chunks.append(chunk)

            Chunk.objects.bulk_update(chunks, ["token_counts"], batch_size=250)
            lemma_syncer.print_execution_status()


@shared_task
def async_bulk_count_lemmas():
    lemmas = {word: _lemma for word, _lemma in Word.objects.values_list("text", "lemma__text")}
    stemmer = SnowballStemmer(language="english")

    for book in Book.objects.all():
        status = book.status()

        if status["chunk_has_token"] > status["chunk_has_lemma"]:
            chunks = []
            lemma_counts = []

            for chunk in (
                book.chunks.exclude(token_counts__isnull=True)
                .filter(lemma_counts__isnull=True)
                .order_by("id")
                .only("token_counts")
            ):
                chunk.lemma_counts = Counter()
                for token, count in chunk.token_counts.items():
                    if token in lemmas:
                        stem = stemmer.stem(lemmas[token])
                        if len(stem) > 2:
                            chunk.lemma_counts.update({stem: count})

                if chunk.lemma_counts:
                    lemma_counts.append(Counter(chunk.lemma_counts))
                    chunk.lemma_counts = dict(chunk.lemma_counts)
                    chunks.append(chunk)

            Chunk.objects.bulk_update(chunks, fields=["lemma_counts"], batch_size=250)
            book.text_lemma_counts = dict(sum(lemma_counts, Counter()))
            book.save(update_fields=["text_lemma_counts"])
            r.post(
                RELENTROPYGETTER_URL + "/books/",
                {"id": book.gutenberg_id, "title": book.title, "author": book.author},
            )


@shared_task
def async_count_lemmas(gutenberg_id):
    book = Book.objects.get(gutenberg_id=gutenberg_id)

    lemmas = {word: _lemma for word, _lemma in Word.objects.values_list("text", "lemma__text")}
    stemmer = SnowballStemmer(language="english")

    chunks = []
    lemma_counts = []
    for chunk in book.chunks.order_by("id").only("token_counts"):
        chunk.lemma_counts = Counter()
        for token, count in chunk.token_counts.items():
            if token in lemmas:
                stem = stemmer.stem(lemmas[token])
                if len(stem) > 2:
                    chunk.lemma_counts.update({stem: count})

        if chunk.lemma_counts:
            lemma_counts.append(Counter(chunk.lemma_counts))
            chunk.lemma_counts = dict(chunk.lemma_counts)
            chunks.append(chunk)

    Chunk.objects.bulk_update(chunks, fields=["lemma_counts"], batch_size=250)
    book.text_lemma_counts = dict(sum(lemma_counts, Counter()))
    book.save(update_fields=["text_lemma_counts"])
    r.post(
        RELENTROPYGETTER_URL + "/books/",
        {"id": book.gutenberg_id, "title": book.title, "author": book.author},
    )
