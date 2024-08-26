from typing import List

from copyright2 import files as fi
from copyright2 import timestamps as ts


def test_notice_pattern() -> None:
    template = "copyright.*?{ts}"
    pattern = fi.notice_pattern(template)
    match = pattern.search("copyright 2020-2,4")
    assert match is not None
    assert match.group("ts") == "2020-2,4"


def prepare_file(s: str) -> List[str]:
    return s.lstrip().splitlines(keepends=True)


class TestScanner:
    def test_scan(self) -> None:
        file = prepare_file(
            r'''
"""This is an example title.

And an example description before some arbitrary copyright notice.

This work belongs to Connor Newton (c) 2020-2,4 and so on.
"""

def main():
  # Do a thing.
  print("hello world!")
'''
        )

        sc = fi.Scanner(fi.notice_pattern(r"Connor Newton \(c\) {ts}"))

        assert tuple(sc.scan(file)) == (
            fi.Notice(5, 21, 47, 39, 47, tuple(ts.tokenize("2020-2,4"))),
        )


class TestAnalyzer:
    def test_analyze_default_is_no_changes(self) -> None:
        az = fi.Analyzer()

        # Would simplify.
        notice = fi.Notice(5, 21, 47, 39, 47, tuple(ts.tokenize("2020-2,3,4")))

        assert tuple(az.analyse((notice,))) == ()

    def test_analyze_ts_simplify(self) -> None:
        az = fi.Analyzer(ts_simplify=True)

        notice = fi.Notice(5, 21, 47, 39, 47, tuple(ts.tokenize("2020-2,3,4")))

        assert tuple(az.analyse((notice,))) == (
            fi.Update(
                notice,
                ("simplified timestamp expression",),
                (ts.Int(2020), "-", ts.Int(4)),
            ),
        )

    def test_analyze_ts_add(self) -> None:
        az = fi.Analyzer(ts_add=(2024, 2025))

        notice = fi.Notice(5, 21, 47, 39, 47, tuple(ts.tokenize("2020-3")))

        assert tuple(az.analyse((notice,))) == (
            fi.Update(
                notice,
                ("added year 2024 to timestamp", "added year 2025 to timestamp"),
                (ts.Int(2020), "-", ts.Int(5)),
            ),
        )


def test_apply() -> None:
    initial = prepare_file(
        r'''
"""This is an example title.

And an example description before some arbitrary copyright notice.

This work belongs to Connor Newton (c) 2020-2,3,4 and so on.
"""

def main():
  # Do a thing.
  print("hello world!")
'''
    )

    want = prepare_file(
        r'''
"""This is an example title.

And an example description before some arbitrary copyright notice.

This work belongs to Connor Newton (c) 2020-4 and so on.
"""

def main():
  # Do a thing.
  print("hello world!")
'''
    )

    updates = (
        fi.Update(
            fi.Notice(5, 21, 47, 39, 49, tuple(ts.tokenize("2020-2,3,4"))),
            (),
            (ts.Int(2020), "-", ts.Int(4)),
        ),
    )

    assert list(fi.apply(initial, updates)) == want
