import random
import string
from decimal import Decimal
from itertools import chain, islice
from typing import Iterable, List, Union, TypeVar

T = TypeVar("T")


def chunks(iterable: Iterable, size=10) -> List[Iterable]:
    iterator = iter(iterable)
    for first in iterator:
        yield chain([first], islice(iterator, size - 1))


def flatten(lst: Iterable[List[T]]) -> List[T]:
    return list(item for sublist in lst for item in sublist)


def random_string(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


def to_dollars(cents: int) -> Decimal:
    return Decimal(cents) / 100


def to_cents(dollars: Union[float, Decimal]) -> int:
    cents = dollars * 100

    return int(cents)
