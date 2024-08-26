from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, List, Tuple, Type, TypeVar

import yaml
from marshmallow import Schema
from marshmallow_dataclass import add_schema

T = TypeVar("T")
U = TypeVar("U")


def first_not_none(a: T | None, b: U | None = None) -> T | U | None:
    if a is not None:
        return a
    if b is not None:
        return b
    return None


@add_schema
@dataclass
class Config:
    Schema: ClassVar[Type[Schema]]

    root: bool = False
    copyright: str | None = None
    include_files: List[str] | None = None
    exclude_files: List[str] | None = None
    include_dirs: List[str] | None = None
    exclude_dirs: List[str] | None = None
    simplify: bool | None = None
    exact: bool | None = None
    add_now: bool | None = None
    git_diff_working: bool | None = None
    git_diff_staged: bool | None = None

    def __or__(self, other) -> Config:
        if not isinstance(other, Config):
            return NotImplemented
        return merge(self, other)


DEFAULTS = Config(
    include_files=[],
    exclude_files=[],
    include_dirs=[],
    exclude_dirs=[],
    simplify=False,
    exact=False,
    add_now=False,
    git_diff_working=True,
    git_diff_staged=True,
)


def merge(base: Config, other: Config) -> Config:
    return Config(
        root=other.root,  # Never inherit.
        copyright=first_not_none(other.copyright, base.copyright),
        include_files=first_not_none(other.include_files, base.include_files),
        exclude_files=first_not_none(other.exclude_files, base.exclude_files),
        include_dirs=first_not_none(other.include_dirs, base.include_dirs),
        exclude_dirs=first_not_none(other.exclude_dirs, base.exclude_dirs),
        simplify=first_not_none(other.simplify, base.simplify),
        exact=first_not_none(other.exact, base.exact),
        add_now=first_not_none(other.add_now, base.add_now),
        git_diff_working=first_not_none(other.git_diff_working, base.git_diff_working),
        git_diff_staged=first_not_none(other.git_diff_staged, base.git_diff_staged),
    )


RC_NAME = ".copyrightrc.yaml"


def load(path: Path) -> Config:
    text = path.read_text()

    json = yaml.safe_load(text)

    return Config.Schema().load(json)


class NoRootError(Exception): ...


def from_root(path: Path) -> Config:
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    cfg = Config()

    dir = path if path.is_dir() else path.parent

    while True:
        base = for_dir(dir, from_root=False)

        cfg = base | cfg  # Under-load parent config.

        if base.root:
            cfg.root = True
            return cfg

        if dir.parent == dir:
            raise NoRootError(f"root config for {path} not found")

        dir = dir.parent


_from_root = from_root


def for_dir(dir: Path, from_root: bool = True) -> Config:
    if not dir.is_dir():
        raise NotADirectoryError(f"{dir} is not a directory")

    if from_root:
        return _from_root(dir)
    else:
        path = dir / RC_NAME

        if path.is_file():
            return load(path)

        return Config()


def for_file(file: Path, from_root: bool = True) -> Config:
    if not file.is_file():
        raise FileNotFoundError(f"{file} is not a file")

    return for_dir(file.parent, from_root)


def for_path(path: Path) -> Config:
    return (for_dir if path.is_dir() else for_file)(path)
