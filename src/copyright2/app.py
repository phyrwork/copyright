import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator, Tuple

import click as cli

from . import configs as cfg
from . import files as f
from . import filesystem as fs


class Context:
    def __init__(self, cfg: cfg.Config):
        self.cfg = cfg


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


@cli.group
def main() -> None: ...


_list = list


@main.command
@cli.argument(
    "path",
    type=cli.Path(exists=True, path_type=Path),
    nargs=-1,
)
def list(path: Tuple[Path, ...]) -> None:
    if len(path) == 0:
        path = (Path("."),)

    app = App(path)

    num_files = 0
    for file in app.list_files():
        cli.echo(file.path)
        num_files += 1

    cli.echo(str(num_files), err=True)


@main.command
@cli.argument(
    "path",
    type=cli.Path(exists=True, path_type=Path),
    nargs=-1,
)
def check(path: Tuple[Path, ...]) -> None:
    if len(path) == 0:
        path = (Path("."),)

    app = App(path)

    num_errs = 0

    def process(file: fs.File) -> None:
        nonlocal num_errs

        if file.cfg.copyright is None:
            cli.echo(f"{file.path}: template not set")
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

        for update in f.Analyzer(
            ts_simplify=file.cfg.simplify, ts_exact=file.cfg.exact
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
@cli.argument(
    "path",
    type=cli.Path(exists=True, path_type=Path),
    nargs=-1,
)
def fix(path: Tuple[Path, ...]) -> None:
    if len(path) == 0:
        path = (Path("."),)

    app = App(path)

    num_errs = 0
    num_fixed = 0

    def process(file: fs.File) -> None:
        nonlocal num_errs
        nonlocal num_fixed

        if file.cfg.copyright is None:
            cli.echo(f"{file.path}: template not set", err=True)
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

        updates = tuple(
            f.Analyzer(ts_simplify=file.cfg.simplify, ts_exact=file.cfg.exact).analyse(
                notices
            )
        )

        if not updates:
            return

        cli.echo(f"fixing {file.path}...", nl=False)

        with open(file.path) as text, NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.writelines(f.apply(text, updates))

        os.rename(tmp.name, file.path)
        cli.echo(f" ok")
        num_fixed += 1

    for i, file in enumerate(app.list_files(), start=1):
        process(file)

    cli.echo(str(num_fixed), err=True)

    if num_errs:
        exit(1)


if __name__ == "__main__":
    main()
