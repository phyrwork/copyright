from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copytree

from click.testing import CliRunner
from pytest import MonkeyPatch, fixture

from copyright2.app import list, check, fix


__DIR__ = Path(__file__).parent


EXAMPLES = __DIR__.parent / "examples"


@contextmanager
def clone_example(monkeypatch: MonkeyPatch, name: str) -> Iterator[None]:
    with TemporaryDirectory() as _dir:
        dir = Path(_dir)
        copytree(EXAMPLES / name, dir / name)
        monkeypatch.chdir(dir / name)
        yield


@fixture
def examples_readme(monkeypatch: MonkeyPatch) -> Iterator[None]:
    with clone_example(monkeypatch, "readme"):
        yield


@fixture
def examples_subdirs(monkeypatch: MonkeyPatch) -> Iterator[None]:
    with clone_example(monkeypatch, "subdirs"):
        yield


def test_list_readme(examples_readme: None) -> None:
    result = CliRunner().invoke(list)

    assert result.exit_code == 0

    assert result.stdout.splitlines() == [
        "README.md",
        "src/ext/readme.c",
        "src/ext/readme.h",
        "src/readme.py",
        "4",
    ]


def test_check_readme(examples_readme: None) -> None:
    result = CliRunner().invoke(check)

    assert result.exit_code != 0

    assert result.stdout.splitlines() == [
        "README.md: notice not found",
        "src/ext/readme.h: 2: simplified timestamp expression",
        "2",
    ]


def test_fix_readme(examples_readme: None) -> None:
    result = CliRunner().invoke(fix)

    assert result.exit_code != 0

    assert result.stdout.splitlines() == [
        "README.md: notice not found",
        "fixing src/ext/readme.h... ok",
        "1",
    ]


def test_list_subdirs(examples_subdirs: None) -> None:
    result = CliRunner().invoke(list)

    assert result.exit_code == 0

    assert result.stdout.splitlines() == [
        "a/b/included.py",
        "1",
    ]
