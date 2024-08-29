import os
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Iterable, Iterator, Literal, Set, Tuple, TypeAlias
from typing import get_args as typing_get_args

import click as cli

from . import files as f
from . import filesystem as fs
from . import git


class FilePathFinder(fs.PathFinder):
    def find(self, args: Tuple[str, ...]) -> Iterable[Path]:
        if not args:
            args = (".",)
        return map(Path, args)


PathFinderType: TypeAlias = Literal["file", "git"]


PATH_FINDER_TYPES: Tuple[PathFinderType, ...] = typing_get_args(PathFinderType)


def find_path(
    find_path_type: PathFinderType,
    find_path_args: Tuple[str, ...],
    git_path_working: bool,
    git_path_staged: bool,
) -> Iterable[Path]:
    finder: fs.PathFinder

    if find_path_type == "file":
        finder = FilePathFinder()
    elif find_path_type == "git":
        finder = git.PathFinder(git_path_working, git_path_staged)
    else:
        raise TypeError(find_path_type)

    return finder.find(find_path_args)


class App:
    def __init__(self, path: Tuple[Path, ...]) -> None:
        self.path = path

    def list_files(self) -> Iterator[fs.File]:
        for path in fs.reduce_path(self.path):
            for file in fs.iter(path):
                if file.path.is_file():
                    yield file

    def count_files(self) -> int:
        return sum(1 for _ in self.list_files())


def path_options(f: Callable[..., Any]) -> Callable[..., Any]:
    f = cli.option(
        "--find-path",
        "find_path_type",
        type=cli.Choice(PATH_FINDER_TYPES),
        default="file",
    )(f)
    f = cli.option(
        "--git-path-working/--no-git-path-working",
        "git_path_working",
        default=True,
    )(f)
    f = cli.option(
        "--git-path-staged/--no-git-path-staged",
        "git_path_staged",
        default=True,
    )(f)
    f = cli.argument(
        "find_path_args",
        type=str,
        nargs=-1,
    )(f)
    return f


def file_options(f: Callable[..., Any]) -> Callable[..., Any]:
    f = cli.option(
        "--add-year",
        "-a",
        "add_year",
        type=int,
        multiple=True,
    )(f)
    f = cli.option(
        "--add-now/--no-add-now",
        "add_now",
        default=False,
    )(f)
    return f


@cli.group
def main() -> None: ...


_list = list


@main.command
@path_options
def list(
    find_path_type: PathFinderType,
    find_path_args: Tuple[str, ...],
    git_path_working: bool,
    git_path_staged: bool,
) -> None:
    path = tuple(
        find_path(find_path_type, find_path_args, git_path_working, git_path_staged)
    )

    app = App(path)

    num_files = 0
    for file in app.list_files():
        cli.echo(file.path)
        num_files += 1

    cli.echo(str(num_files), err=True)


@main.command
@path_options
@file_options
def check(
    find_path_type: PathFinderType,
    find_path_args: Tuple[str, ...],
    git_path_working: bool,
    git_path_staged: bool,
    add_year: Tuple[int, ...],
    add_now: bool,
) -> None:
    path = tuple(
        find_path(find_path_type, find_path_args, git_path_working, git_path_staged)
    )

    app = App(path)

    num_errs = 0

    def process(file: fs.File) -> None:
        nonlocal num_errs

        if file.cfg.copyright is None:
            cli.echo(f"{file.path}: copyright not set")
            num_errs += 1
            return

        with open(file.path) as text:
            # TODO: Single-buffer iterator to allow determining non-zero length
            #  without buffering all into a lift.
            notices = _list(f.Scanner(f.notice_pattern(file.cfg.copyright)).scan(text))

        if not notices:
            cli.echo(f"{file.path}: notice not found")
            num_errs += 1
            return

        ts_add: Set[int] = set(*add_year)

        if add_now or file.cfg.add_now:
            ts_add.add(datetime.now().year)

        for update in f.Analyzer(
            ts_simplify=file.cfg.simplify or False,
            ts_exact=file.cfg.exact or False,
            ts_add=tuple(ts_add),
        ).analyse(notices):
            for change in update.changes:
                cli.echo(f"{file.path}: {update.notice.lineno}: {change}")
                num_errs += 1

    for i, file in enumerate(app.list_files(), start=1):
        process(file)

    cli.echo(str(num_errs), err=True)

    if num_errs:
        exit(1)


@main.command
@path_options
@file_options
def fix(
    find_path_type: PathFinderType,
    find_path_args: Tuple[str, ...],
    git_path_working: bool,
    git_path_staged: bool,
    add_year: Tuple[int, ...],
    add_now: bool,
) -> None:
    path = tuple(
        find_path(find_path_type, find_path_args, git_path_working, git_path_staged)
    )

    app = App(path)

    num_errs = 0
    num_fixed = 0

    def process(file: fs.File) -> None:
        nonlocal num_errs
        nonlocal num_fixed

        if file.cfg.copyright is None:
            cli.echo(f"{file.path}: copyright not set", err=True)
            num_errs += 1
            return

        with open(file.path) as text:
            # TODO: Single-buffer iterator to allow determining non-zero length
            #  without buffering all into a lift.
            notices = _list(f.Scanner(f.notice_pattern(file.cfg.copyright)).scan(text))

        if not notices:
            cli.echo(f"{file.path}: notice not found", err=True)
            num_errs += 1
            return

        ts_add: Set[int] = set(*add_year)

        if add_now or file.cfg.add_now:
            ts_add.add(datetime.now().year)

        updates = tuple(
            f.Analyzer(
                ts_simplify=file.cfg.simplify or False,
                ts_exact=file.cfg.exact or False,
                ts_add=tuple(ts_add),
            ).analyse(notices)
        )

        if not updates:
            return

        cli.echo(f"fixing {file.path}...", nl=False)

        with open(file.path) as text, NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.writelines(f.apply(text, updates))

        os.rename(tmp.name, file.path)
        cli.echo(" ok")
        num_fixed += 1

    for i, file in enumerate(app.list_files(), start=1):
        process(file)

    cli.echo(str(num_fixed), err=True)

    if num_errs:
        exit(1)


if __name__ == "__main__":
    main()
