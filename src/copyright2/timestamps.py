from __future__ import annotations

import re
from functools import cached_property, reduce
from itertools import chain, zip_longest
from typing import Iterable, Iterator, Literal, Set, Tuple, TypeAlias, Union


class Int(int):
    @cached_property
    def digits(self) -> Tuple[int, ...]:
        if self == 0:
            return ()
        return tuple(int(c) for c in str(self))

    @classmethod
    def from_digits(cls, digits: Iterable[int]) -> Int:
        s = "".join(map(str, digits))
        i = int(s) if s else 0
        return Int(i)

    def __getitem__(self, o: int) -> int:
        return self.digits[o]

    def __iter__(self) -> Iterator[int]:
        return iter(self.digits)

    def __len__(self) -> int:
        return len(self.digits)

    @property
    def msf(self) -> int:
        return self[0]

    @property
    def lsf(self) -> int:
        return self[-1]

    def __and__(self, other: int) -> Int:
        if not isinstance(other, Int):
            other = Int(other)

        if other == self:
            return self

        if len(self) != len(other):
            return Int(0)

        o = 0
        for o, ab in enumerate(zip(self, other)):
            a, b = ab
            if a != b:
                break

        return Int.from_digits(  # type:ignore[no-any-return]  # mypy bug?
            self.digits[:o]
        ) * 10 ** (len(self.digits) - o)

    def __xor__(self, other: int) -> Int:
        if not isinstance(other, Int):
            other = Int(other)

        if other == self:
            return Int(0)

        if len(self.digits) != len(other.digits):
            return self

        o = 0
        for o, ab in enumerate(zip(self.digits, other.digits)):
            a, b = ab
            if a != b:
                break

        return Int.from_digits(self.digits[o:])

    def __or__(self, other: int) -> Int:
        if not isinstance(other, Int):
            other = Int(other)

        if other == self:
            return self

        if len(other.digits) > len(self.digits):
            return other

        digits = list(self.digits)
        for o, b in enumerate(reversed(other.digits), start=1):
            digits[-o] = b

        return Int.from_digits(digits)


Token: TypeAlias = Union[Int, Literal["-", ","]]


PATTERN = re.compile(r"\d+(-\d+)?(,\s*\d+(-\d+)?)*")


def tokenize(s: Iterable[str]) -> Iterator[Token]:
    ds = ""  # Digits buffer.

    for o, c in enumerate(s):
        # Whitespace is meaningless.
        # TODO: Or not... might be useful to detect changes in formatting.
        if str.isspace(c):
            continue

        # Collect digits...
        if "0" <= c <= "9":
            ds += c
            continue
        # ...and emit as int token.
        if ds:
            yield Int(ds)
            ds = ""

        # Emit separators.
        if c == ",":
            yield ","
        elif c == "-":
            yield "-"
        else:
            raise ValueError(f"unexpected char '{c}' at position {o}")

    if ds:
        yield Int(ds)


class Range(Tuple[int, int]):
    @property
    def start(self) -> int:
        return self[0]

    @property
    def end(self) -> int:
        return self[1]

    @classmethod
    def point(cls, i: int) -> Range:
        return Range((i, i))

    def __str__(self) -> str:
        if self.start == self.end:
            return str(self.start)

        return f"{self.start}-{self.end}"

    def __or__(self, other: Range) -> Range | None:
        if self < other:
            a, b = self, other
        else:
            a, b = other, self

        if b.start <= a.end + 1:
            return Range((a.start, b.end))

        return None


def parse(tokens: Iterable[Token]) -> Iterator[Range]:
    it = enumerate(tokens)

    o, tok = next(it, (0, None))
    if tok is None:
        return

    start = Int(tok)

    bases = [start]

    for o, tok in it:
        if isinstance(tok, int):
            raise ValueError(f"expected operator, got '{tok}' at position {o}")

        op = tok

        o, end = next(it, (o, None))
        if end is None:
            raise ValueError(f"expected int, got EOF at position {o}")
        if not isinstance(end, Int):
            raise ValueError(f"expected int, got '{end}' at position {o}")

        if op == ",":
            if start:
                yield Range.point(reduce(lambda a, b: b | a, reversed(bases), start))

            # Eject bases that are shorter than the new one to allow escaping from lower
            # orders.
            while bases and len(end) >= bases[-1]:
                bases.pop()

            bases.append(end)
            start = end

        elif op == "-":
            end = bases[-1] | end

            # fmt: off
            yield Range((
                reduce(lambda a, b: b | a, reversed(bases), bases[-1]),
                reduce(lambda a, b: b | a, reversed(bases), end),
            ))
            # fmt: on

            start = Int(0)

    if start:
        yield Range.point(reduce(lambda a, b: b | a, reversed(bases), start))


def parses(s: Iterable[str]) -> Iterator[Range]:
    return parse(tokenize(s))


def simplify(ranges: Iterable[Range], sort: bool = True) -> Iterator[Range]:
    if sort:
        ranges = sorted(ranges)

    ranges = iter(ranges)

    base = next(ranges, None)
    if base is None:
        return

    for other in ranges:
        both = base | other

        if both:
            # Stack intersecting ranges...
            base = both

        else:
            # ...or emit the last and keep the current.
            yield base
            base = other

    yield base


def equals(*ts: Iterable[Range]) -> bool:
    for ranges in zip_longest(*ts):
        if len(set(ranges)) != 1:
            return False
    return True


def explode(ranges: Iterable[Range]) -> Set[int]:
    return set(
        chain.from_iterable(range(range_.start, range_.end + 1) for range_ in ranges)
    )


def join(years: Iterable[int], sort: bool = True) -> Iterator[Range]:
    if sort:
        years = sorted(years)

    years = iter(years)
    start = next(years, None)

    if start is None:
        return

    end = start

    for year in years:
        if year != end + 1:
            yield Range((start, end))
            end = start = year
        else:
            end = year

    yield Range((start, end))


def compile(ranges: Iterable[Range], sort: bool = True) -> Iterator[Token]:
    if sort:
        ranges = sorted(ranges)

    ranges = iter(ranges)

    range = next(ranges, None)
    if range is None:
        return

    start, end = range

    yield Int(start)
    base = Int(start)

    if end != start:
        yield "-"
        yield Int(end) ^ base

    for start, end in ranges:
        yield ","
        yield Int(start) ^ base

        if start != end:
            base = Int(end)
            yield "-"
            yield Int(end) ^ Int(start)
