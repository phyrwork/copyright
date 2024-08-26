from pathlib import Path

EXAMPLES = Path(__file__).parent.parent / "examples"

if not EXAMPLES.is_dir():
    raise ValueError(f"examples directory {EXAMPLES.resolve()} not found")

from copyright2 import configs as cfg
from copyright2 import filesystem as fs


def test_iter_subdirs_example() -> None:
    files = {}
    for file in fs.iter(EXAMPLES / "subdirs"):
        files[file.path] = file.cfg

    root = cfg.DEFAULTS | cfg.Config(
        root=True,
        copyright="Copyright (c) {intervals}",
        include_dirs=[".*"],
        exclude_dirs=[],
        include_files=[".*\.py"],
        exclude_files=[],
    )

    a = root | cfg.Config()

    b = a | cfg.Config(exclude_files=["excluded\.py"])

    assert files == {
        EXAMPLES / "subdirs": root,
        EXAMPLES / "subdirs/a": a,
        EXAMPLES / "subdirs/a/b": b,
        EXAMPLES / "subdirs/a/b/included.py": b,
    }
