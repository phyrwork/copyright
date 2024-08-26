from copyright2 import configs


def test_merge_root_not_inherited() -> None:
    base = configs.Config(root=True)
    other = configs.Config()
    assert base | other == configs.Config(root=False)


def test_merge_copyright_inherited() -> None:
    base = configs.Config(copyright="base")
    other = configs.Config()
    assert base | other == configs.Config(copyright="base")


def test_merge_copyright_replaced() -> None:
    base = configs.Config(copyright="base")
    other = configs.Config(copyright="other")
    assert base | other == configs.Config(copyright="other")


def test_merge_include_files_inherited() -> None:
    base = configs.Config(include_files=["base"])
    other = configs.Config()
    assert base | other == configs.Config(include_files=["base"])


def test_merge_include_files_replaced() -> None:
    base = configs.Config(include_files=["base"])
    other = configs.Config(include_files=["other"])
    assert base | other == configs.Config(include_files=["other"])


def test_merge_exclude_files_inherited() -> None:
    base = configs.Config(exclude_files=["base"])
    other = configs.Config()
    assert base | other == configs.Config(exclude_files=["base"])


def test_merge_exclude_files_replaced() -> None:
    base = configs.Config(exclude_files=["base"])
    other = configs.Config(exclude_files=["other"])
    assert base | other == configs.Config(exclude_files=["other"])


def test_merge_include_dirs_inherited() -> None:
    base = configs.Config(include_dirs=["base"])
    other = configs.Config()
    assert base | other == configs.Config(include_dirs=["base"])


def test_merge_include_dirs_replaced() -> None:
    base = configs.Config(include_dirs=["base"])
    other = configs.Config(include_dirs=["other"])
    assert base | other == configs.Config(include_dirs=["other"])


def test_merge_exclude_dirs_inherited() -> None:
    base = configs.Config(exclude_dirs=["base"])
    other = configs.Config()
    assert base | other == configs.Config(exclude_dirs=["base"])


def test_merge_exclude_dirs_replaced() -> None:
    base = configs.Config(exclude_dirs=["base"])
    other = configs.Config(exclude_dirs=["other"])
    assert base | other == configs.Config(exclude_dirs=["other"])
