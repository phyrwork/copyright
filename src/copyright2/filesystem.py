from __future__ import annotations

import re
from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List, Protocol, Tuple

from . import configs


@dataclass
class Filter:
    include_files: List[str] = field(default_factory=list)
    exclude_files: List[str] = field(default_factory=list)
    include_dirs: List[str] = field(default_factory=list)
    exclude_dirs: List[str] = field(default_factory=list)

    def match(self, path: Path) -> bool:
        include_files = self.include_dirs if path.is_dir() else self.include_files
        exclude_files = self.exclude_dirs if path.is_dir() else self.exclude_files

        for pattern in exclude_files:
            if re.search(pattern, str(path)):
                return False

        for pattern in include_files:
            if re.search(pattern, str(path)):
                return True

        return False


@dataclass
class File:
    path: Path
    cfg: configs.Config

    def __iter__(self) -> Iterator[File]:
        # Emit parents first.
        yield self

        if not self.path.is_dir():
            return

        if self.cfg.include_files is None:
            raise ValueError  # TODO:
        if self.cfg.exclude_files is None:
            raise ValueError  # TODO:
        if self.cfg.include_dirs is None:
            raise ValueError  # TODO:
        if self.cfg.exclude_dirs is None:
            raise ValueError  # TODO:

        # Do not emit or search files or directories that
        # - Don't match any include pattern.
        # - Do match any exclude pattern.
        filter = Filter(
            include_files=self.cfg.include_files,
            exclude_files=self.cfg.exclude_files,
            include_dirs=self.cfg.include_dirs,
            exclude_dirs=self.cfg.exclude_dirs,
        )

        for path in sorted(self.path.iterdir()):
            if not filter.match(path):
                continue

            config = self.cfg

            # Merge configuration from subdirectories.
            if path.is_dir():
                config |= configs.for_dir(path, from_root=False)

            yield from File(path, config)


def iter(path: Path) -> Iterator[File]:
    config = configs.DEFAULTS | configs.for_path(path)

    if config.include_files is None:
        raise ValueError  # TODO:
    if config.exclude_files is None:
        raise ValueError  # TODO:
    if config.include_dirs is None:
        raise ValueError  # TODO:
    if config.exclude_dirs is None:
        raise ValueError  # TODO:

    filter = Filter(
        include_files=config.include_files,
        exclude_files=config.exclude_files,
        include_dirs=config.include_dirs,
        exclude_dirs=config.exclude_dirs,
    )

    if not filter.match(path):
        return

    yield from File(path, config)


def reduce_path(path: Iterable[Path]) -> Iterator[Path]:
    # TODO: Do better than O(N^2)
    for subj in path:
        emit = True
        for other in path:
            if other is subj:
                continue
            if subj.is_relative_to(other):
                emit = False
                break
        if emit:
            yield subj


class PathFinder(Protocol):
    @abstractmethod
    def find(self, args: Tuple[str, ...]) -> Iterable[Path]: ...
