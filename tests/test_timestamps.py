from typing import Iterable, Sequence

from pytest import mark, param

from copyright2 import timestamps as ts


class TestInt:
    @mark.parametrize(
        ["ds", "i"],
        [
            param((1, 2, 3, 4, 5), 12345, id="tuple"),
            param([1, 2, 3, 4, 5], 12345, id="list"),
            param(iter((1, 2, 3, 4, 5)), 12345, id="iterator"),
            param((), 0, id="zero"),
            param((1,), 1, id="one"),
            param((0, 1, 2, 3, 4), 1234, id="leading-zero"),
            param((4, 3, 2, 1, 0), 43210, id="trailing-zero"),
        ],
    )
    def test_from_digits(self, ds: Iterable[int], i: int) -> None:
        assert ts.Int.from_digits(ds) == i

    def test_msf(self) -> None:
        assert ts.Int(1234).msf == 1

    def test_lsf(self) -> None:
        assert ts.Int(1234).lsf == 4

    @mark.parametrize(
        ["base", "other", "want"],
        [
            param(123, 12, 0, id="shorter"),
            param(12, 123, 0, id="longer"),
            param(123, 123, 123, id="equal"),
            param(123, 120, 120, id="lesser"),
            param(120, 123, 120, id="greater"),
        ],
    )
    def test_and(self, base: int, other: int, want: int) -> None:
        assert ts.Int(base) & other == want

    @mark.parametrize(
        ["base", "other", "want"],
        [
            param(123, 12, 123, id="shorter"),
            param(12, 123, 12, id="longer"),
            param(123, 123, 0, id="equal"),
            param(123, 120, 3, id="lesser"),
            param(120, 123, 0, id="greater"),
        ],
    )
    def test_xor(self, base: int, other: int, want: int) -> None:
        assert ts.Int(base) ^ other == want

    @mark.parametrize(
        ["base", "other", "want"],
        [
            param(123, 12, 112, id="shorter"),
            param(12, 123, 123, id="longer"),
            param(123, 123, 123, id="equal"),
            param(123, 120, 120, id="lesser"),
            param(120, 123, 123, id="greater"),
        ],
    )
    def test_or(self, base: int, other: int, want: int) -> None:
        assert ts.Int(base) | other == want


@mark.parametrize(
    ["s", "tokens"],
    [
        param("1", (1,), id="one-digit"),
        param("12", (12,), id="many-digits"),
        param(",", (",",), id="sequence-operator"),
        param("-", ("-",), id="range-operator"),
        param("2024,5", (2024, ",", 5), id="sequence"),
        param("2024-5", (2024, "-", 5), id="range"),
    ],
)
def test_tokenize(s: Iterable[str], tokens: Sequence[str]) -> None:
    assert tuple(ts.tokenize(s)) == tuple(tokens)


@mark.parametrize(
    ["tokens", "want"],
    [
        param(
            (ts.Int(2019), ",", ts.Int(2020), ",", ts.Int(2021)),
            (
                ts.Range.point(2019),
                ts.Range.point(2020),
                ts.Range.point(2021),
            ),
            id="sequence-order-equal",
        ),
        param(
            (ts.Int(2019), ",", ts.Int(20), ",", ts.Int(21)),
            (
                ts.Range.point(2019),
                ts.Range.point(2020),
                ts.Range.point(2021),
            ),
            id="sequence-order-lesser",
        ),
        param(
            (ts.Int(2019), "-", ts.Int(2021)),
            (ts.Range((2019, 2021)),),
            id="range-order-equal",
        ),
        param(
            (ts.Int(2019), "-", ts.Int(21)),
            (ts.Range((2019, 2021)),),
            id="range-order-lesser",
        ),
        param(
            (ts.Int(2018), "-", ts.Int(2019), ",", ts.Int(2021)),
            (
                ts.Range((2018, 2019)),
                ts.Range.point(2021),
            ),
            id="reset-order-sequence",
        ),
        param(
            (ts.Int(793), ",", ts.Int(1066), "-", ts.Int(1067)),
            (
                ts.Range.point(793),
                ts.Range((1066, 1067)),
            ),
            id="reset-order-range",
        ),
        param(
            (
                ts.Int(2007),
                "-",
                ts.Int(8),
                ",",
                ts.Int(10),
                "-",
                ts.Int(1),
                ",",
                ts.Int(7),
                "-",
                ts.Int(9),
                ",",
                ts.Int(20),
                "-",
                ts.Int(1),
            ),
            (
                ts.Range((2007, 2008)),
                ts.Range((2010, 2011)),
                ts.Range((2017, 2019)),
                ts.Range((2020, 2021)),
            ),
            id="reset-order-complex",
        ),
    ],
)
def test_parse(tokens: Iterable[ts.Token], want: Sequence[ts.Range]) -> None:
    assert tuple(ts.parse(tokens)) == tuple(want)


@mark.parametrize(
    ["s", "want"],
    [
        param("0", True, id="one-digit"),
        param("00", True, id="many-digits"),
        param("0,0", True, id="two-digit-sequence"),
        param("0,0,0", True, id="three-digit-sequence"),
        param("0-0", True, id="range"),
        param("0-0,0-0", True, id="range-sequence"),
        param("0-0-0", False, id="three-point-range"),
        param("0,", False, id="unterminated-sequence"),
        param("0-", False, id="unterminated-range"),
    ],
)
def test_pattern(s: str, want: bool) -> None:
    assert bool(ts.PATTERN.fullmatch(s)) == want


@mark.parametrize(
    ["initial", "want"],
    [
        param(
            (ts.Range((1, 2)), ts.Range((5, 6))),
            (ts.Range((1, 2)), ts.Range((5, 6))),
            id="disjoint",
        ),
        param(
            (ts.Range((1, 2)), ts.Range((3, 4))),
            (ts.Range((1, 4)),),
            id="contiguous",
        ),
        param(
            (ts.Range((1, 2)), ts.Range((2, 3))),
            (ts.Range((1, 3)),),
            id="joint",
        ),
    ],
)
def test_simplify(initial: Iterable[ts.Range], want: Iterable[ts.Range]) -> None:
    assert tuple(ts.simplify(initial)) == tuple(want)


@mark.parametrize(
    ["items", "equal"],
    [
        param((), True, id="no-ts"),
        param(
            ((ts.Range((1, 2)),), (ts.Range((1, 2)),)),
            True,
            id="equal-pair",
        ),
        param(
            ((ts.Range((1, 2)),), (ts.Range((1, 2)),), (ts.Range((1, 2)),)),
            True,
            id="equal-triple",
        ),
        param(
            ((ts.Range((1, 2)),), (ts.Range((1, 3)),)),
            False,
            id="unequal-pair",
        ),
    ],
)
def test_equals(items: Iterable[Iterable[ts.Range]], equal: bool) -> None:
    assert ts.equals(*items) is equal


def test_explode() -> None:
    assert ts.explode((ts.Range((1, 2)), ts.Range((4, 6)))) == {1, 2, 4, 5, 6}


@mark.parametrize(
    ["years", "ranges"],
    [
        param(
            range(2020, 2024 + 1),
            (ts.Range((2020, 2024)),),
            id="contiguous",
        ),
        param(
            (2020, 2021, 2023, 2024),
            (ts.Range((2020, 2021)), ts.Range((2023, 2024))),
            id="disjoint",
        ),
    ],
)
def test_join(years: Iterable[int], ranges: Sequence[ts.Range]) -> None:
    assert tuple(ts.join(years)) == tuple(ranges)


@mark.parametrize(
    ["ranges", "tokens"],
    [
        param(
            (ts.Range.point(2007),),
            (ts.Int(2007),),
            id="scalar",
        ),
        param(
            (ts.Range.point(2004), ts.Range.point(2006), ts.Range.point(2008)),
            (ts.Int(2004), ",", ts.Int(6), ",", ts.Int(8)),
            id="sequence-1s",
        ),
        param(
            (ts.Range.point(2008), ts.Range.point(2010), ts.Range.point(2012)),
            (ts.Int(2008), ",", ts.Int(10), ",", ts.Int(12)),
            id="sequence-10s",
        ),
        param(
            (ts.Range((2019, 2021)),),
            (ts.Int(2019), "-", ts.Int(21)),
            id="range-order-equal",
        ),
        param(
            (ts.Range((2009, 2011)),),
            (ts.Int(2009), "-", ts.Int(11)),
            id="range-order-greater",
        ),
        param(
            (ts.Range((2009, 2011)), ts.Range((2012, 2014))),
            (ts.Int(2009), "-", ts.Int(11), ",", ts.Int(12), "-", ts.Int(4)),
            id="range-sequence",
        ),
    ],
)
def test_compile(ranges: Iterable[ts.Range], tokens: Sequence[ts.Token]) -> None:
    assert tuple(ts.compile(ranges)) == tuple(tokens)
