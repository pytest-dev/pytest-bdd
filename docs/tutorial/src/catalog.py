"""This files represents simple `Application under test`"""
from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass  # Easy way to not write redundant __init__ https://docs.python.org/3/library/dataclasses.html
class Book:
    author: str
    title: str


@dataclass
class Catalog:
    storage: List[Book] = field(default_factory=list)

    def add_books_to_catalog(self, books: Iterable[Book]):
        self.storage.extend(books)

    def search_by_author(self, term: str):
        for book in self.storage:
            if term in book.author:
                yield book

    def search_by_title(self, term: str):
        for book in self.storage:
            if term in book.title:
                yield book
