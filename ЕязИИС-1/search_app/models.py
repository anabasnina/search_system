import math
import re
from typing import Final

import pymorphy2
from django.db import models

morph: Final = pymorphy2.MorphAnalyzer()


# Create your models here.

class AbstractDocument(models.Model):
    class Meta:
        abstract = True

    text = models.TextField(default='Sample text')

    def get_words(self):
        words = {}
        for raw_word in self.text.split():
            if raw_word.endswith((',', '.', '-', '!', '?', ';')):
                word = raw_word[:-1]
            else:
                word = raw_word
            word = morph.parse(word)[0].normalized
            if 'PREP' in word.tag:
                continue
            else:
                word = word.word
            if word in words:
                words[word] += 1
            else:
                words[word] = 1
        return words

    def get_tf_idf(self):
        doc_word_dict = self.get_words()
        max_count = 0
        for count in doc_word_dict.values():
            if count > max_count:
                max_count = count
        tf_idf_dict = {}
        for word, idf in Document.get_idf().items():
            if word in doc_word_dict:
                tf_idf_dict[word] = (doc_word_dict[word] / max_count) * idf
            else:
                tf_idf_dict[word] = 0
        return tf_idf_dict

    def get_length(self):
        tf_idf_dict = self.get_tf_idf()
        sum_of_squares = 0
        for value in tf_idf_dict.values():
            sum_of_squares += value ** 2
        return sum_of_squares ** 0.5


class Document(AbstractDocument):
    title = models.CharField(max_length=1000, null=True, default='Title')
    snippet = models.CharField(max_length=500, null=True, default='Sample text')

    @staticmethod
    def get_idf():
        documents = Document.objects.all()
        n = documents.count()
        words_count = {}
        for document in documents:
            for word in set(document.get_words().keys()):
                if word in words_count:
                    words_count[word] += 1
                else:
                    words_count[word] = 1

        words_idf = {}
        for word, p in words_count.items():
            words_idf[word] = math.log2(n / p)
        return words_idf

    def gen_snippet(self, words):
        snippet = ''
        for word in words:
            word = word[:4]
            pattern = r'.{0,50} %s.{0,50}' % word
            results = re.findall(pattern, self.text)
            temp = ''
            for result in results:
                temp += '..'
                if len(temp + result) < 500:
                    temp += result + '..   '
            if len(temp) > len(snippet):
                snippet = temp
        self.snippet = snippet
        self.save()


class Search(AbstractDocument):
    def get_result(self):
        documents = Document.objects.all()
        docs_sim = {}
        search_tf_idf = self.get_tf_idf()
        for doc in documents:
            doc.gen_snippet(self.get_words().keys())
            doc_tf_idf = doc.get_tf_idf()
            numerator = 0
            for word in search_tf_idf:
                numerator += search_tf_idf[word] * doc_tf_idf[word]
            try:
                result = numerator / (self.get_length() * doc.get_length())
                if result != 0:
                    docs_sim[doc] = result
            except ZeroDivisionError:
                return list()
        return sorted(docs_sim, key=docs_sim.get, reverse=True)
