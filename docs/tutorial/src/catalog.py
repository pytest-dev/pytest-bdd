"""This files represents simple `Application under test`"""
from typing import List

from attr import Factory, attrib, attrs


@attrs
class Book:
    author = attrib(type=str)
    title = attrib(type=str)


@attrs
class Catalog:
    storage = attrib(default=Factory(list))

    def add_books_to_catalog(self, books: List[Book]):
        self.storage.extend(books)

    def search_by_author(self, term: str):
        return filter(lambda book: term in book.author, self.storage)

    def search_by_title(self, term: str):
        return filter(lambda book: term in book.title, self.storage)
