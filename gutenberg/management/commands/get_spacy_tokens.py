from collections import Counter

import spacy
from unidecode import unidecode
from django.core.management.base import BaseCommand
from django.db import transaction

from gutenberg.models import Chunk, Lemma, Word


class LemmaSyncer:

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
        lemma_obj = Lemma.objects.filter(text=lemma).first()
        word_obj = Word.objects.filter(text=lemma).first()

        if lemma_obj and word_obj:
            if word_obj.lemma.id != lemma_obj.id:
                if (len(word_obj.lemma.text) < len(lemma_obj.text)) or (
                    word_obj.lemma.words.count() > lemma_obj.words.count()
                ):
                    lemma_obj = self.replace_lemma(
                        old_lemma_obj=lemma_obj, new_lemma_obj=word_obj.lemma
                    )
                else:
                    raise Exception
        elif lemma_obj and not word_obj:
            lemma_obj.words.create(text=lemma)
        elif not lemma_obj and word_obj:
            if len(lemma) < len(word_obj.lemma.text):
                lemma_obj = self.replace_lemma(
                    new_lemma_obj=Lemma.objects.create(text=lemma),
                    old_lemma_obj=word_obj.lemma,
                )
            else:
                lemma_obj = word_obj.lemma

        elif not lemma_obj and not word_obj:
            lemma_obj = Lemma.objects.create(text=lemma)
            lemma_obj.words.create(text=lemma)
        return lemma_obj

    def add(self, lemma, word):

        with transaction.atomic():

            lemma_obj = self.get_or_create_lemma(lemma=lemma)
            word_obj = Word.objects.filter(text=word).first()

            if word_obj:
                if word_obj.lemma.id != lemma_obj.id:
                    new, old = self.sort_lemma(lemma_obj, word_obj.lemma)
                    lemma_obj = self.replace_lemma(old_lemma_obj=old, new_lemma_obj=new)

            else:
                lemma_obj.words.create(text=word)


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):

        nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

        lemma_syncer = LemmaSyncer()

        for chunk in Chunk.objects.filter(token_counts__isnull=True).order_by("id"):
            tokens = []
            for token in nlp(unidecode(chunk.text)):
                if token.is_alpha and not token.is_stop:
                    lemma_syncer.add(lemma=token.lemma_.lower(), word=token.lower_)
                    tokens.append(token.lemma_.lower())
            chunk.token_counts = dict(Counter(tokens))
            print(chunk.token_counts)
            chunk.save(update_fields=["token_counts"])
