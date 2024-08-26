import subprocess
from pathlib import Path
from typing import Iterable, Set, Tuple

from . import filesystem as fs


class PathFinder(fs.PathFinder):
    def __init__(self, working: bool = True, staged: bool = True) -> None:
        self.working = working
        self.staged = staged

    def find(self, args: Tuple[str, ...]) -> Iterable[Path]:
        top = Path(
            subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
            ).stdout.strip()
        )

        files: Set[Path] = set()  # TODO: Ordered

        if self.working:
            files.update(
                map(
                    Path,
                    subprocess.run(
                        ["git", "diff", "--name-only", *args],
                        capture_output=True,
                        text=True,
                    )
                    .stdout.strip()
                    .splitlines(),
                )
            )

        if self.staged:
            files.update(
                map(
                    Path,
                    subprocess.run(
                        ["git", "diff", "--name-only", "--cached", *args],
                        capture_output=True,
                        text=True,
                    )
                    .stdout.strip()
                    .splitlines(),
                )
            )

        cwd = Path(".").absolute()

        for file in files:
            file = top / file  # Relative to Git root
            if file.is_relative_to(cwd):
                yield file.relative_to(cwd)
