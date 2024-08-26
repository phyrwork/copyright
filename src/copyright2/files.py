import re
from dataclasses import dataclass
from functools import cached_property
from typing import Iterable, Iterator, List, NamedTuple, Sequence, Tuple

from . import timestamps as ts


def notice_pattern(template: str) -> re.Pattern[str]:
    return re.compile(template.format(ts=rf"(?P<ts>{ts.PATTERN.pattern})"))


@dataclass(frozen=True)
class Notice:
    lineno: int
    text_start: int
    text_end: int
    ts_start: int
    ts_end: int
    ts_tokens: Tuple[ts.Token, ...]

    @cached_property
    def ts_ranges(self) -> Tuple[ts.Range, ...]:
        return tuple(ts.parse(self.ts_tokens))


class Scanner:
    def __init__(self, pattern: re.Pattern[str]) -> None:
        self.pattern = pattern

    def scan(self, file: Iterable[str]) -> Iterator[Notice]:
        for lineno, line in enumerate(file, start=1):
            if match := self.pattern.search(line):
                text = match[0]
                text_start = match.start()
                text_end = match.end()

                ts_start = match.start("ts")
                ts_end = match.end("ts")
                ts_tokens = tuple(
                    ts.tokenize(text[ts_start - text_start : ts_end - text_start])
                )

                yield Notice(lineno, text_start, text_end, ts_start, ts_end, ts_tokens)


class Update(NamedTuple):
    notice: Notice
    changes: Tuple[str, ...]
    ts_tokens: Tuple[ts.Token, ...]


class Analyzer:
    def __init__(
        self,
        ts_simplify: bool = False,
        ts_exact: bool = False,
        ts_add: Sequence[int] = (),
    ):
        self.ts_simplify = ts_simplify
        self.ts_exact = ts_exact
        self.ts_add = ts_add

    def analyse(self, notices: Iterable[Notice]) -> Iterator[Update]:
        for notice in notices:
            changes: List[str] = []

            # Only update the timestamp if requested or if we changed it.
            ts_join = False
            ts_simplify = False
            ts_compile = False

            # Check whether we would simplify the timestamp before changing it.
            if self.ts_simplify:
                ts_ranges = tuple(ts.simplify(notice.ts_ranges))

                if ts_ranges != notice.ts_ranges:
                    changes.append("simplified timestamp expression")

                ts_simplify = True

            if self.ts_exact:
                ts_tokens = tuple(ts.compile(notice.ts_ranges))

                if ts_tokens != notice.ts_tokens:
                    changes.append("re-formatted timestamp expression")

                ts_compile = True

            # Add years to timestamp.
            ts_years = ts.explode(notice.ts_ranges)

            for year in self.ts_add:
                if year not in ts_years:
                    changes.append(f"added year {year} to timestamp")
                    ts_years.add(year)
                    ts_join = True

            # Re-format timestamp.
            ts_ranges = notice.ts_ranges

            if ts_join:
                ts_ranges = tuple(ts.join(ts_years))
                ts_simplify = True

            if ts_simplify:
                ts_ranges = tuple(ts.simplify(ts_ranges))
                ts_compile = True

            ts_tokens = notice.ts_tokens

            if ts_compile:
                ts_tokens = tuple(ts.compile(ts_ranges))

            # Only emit fixes for updated noticed.
            if changes:
                yield Update(notice, tuple(changes), ts_tokens)


def apply(
    file: Iterable[str], updates: Iterable[Update], sort: bool = True
) -> Iterator[str]:
    if sort:
        updates = sorted(updates, key=lambda update: update.notice.lineno)

    lines = enumerate(file, start=1)

    lineno, line = next(lines, (0, ""))
    if lineno == 0:
        # Empty file.
        return

    for update in updates:
        while lineno != update.notice.lineno:
            yield line
            lineno, line = next(lines)

        ts_text = "".join(map(str, update.ts_tokens))

        yield line[: update.notice.ts_start] + ts_text + line[update.notice.ts_end :]

    for _, line in lines:
        yield line
