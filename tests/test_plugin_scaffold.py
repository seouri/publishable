# tests/test_plugin_scaffold.py
import tomllib
from pathlib import Path

import pytest

from publishable.errors import ContractError
from publishable.plugin_scaffold import package_name, scaffold_plugin

GROUPS = (
    "publishable.templates",
    "publishable.resolvers",
    "publishable.probes",
    "publishable.writers",
    "publishable.readers",
)


def test_the_scaffold_declares_every_group_core_reads(tmp_path: Path):
    """Five registries, one mechanism — `reference.md` § Creating a plugin. A
    scaffold emitting four was already stale the day Part A minted
    `publishable.readers`, so this asserts against `plugins.GROUPS` itself rather
    than against a literal list, which is what keeps a sixth group from shipping a
    scaffold that omits it."""
    from publishable.plugins import GROUPS as CORE_GROUPS

    root = scaffold_plugin(tmp_path / "publishable-my-assay")
    declared = tomllib.loads((root / "pyproject.toml").read_text())
    entry_points = declared["project"]["entry-points"]

    assert set(entry_points) == set(CORE_GROUPS)
    assert set(GROUPS) == set(CORE_GROUPS)  # the literal above is a control on the import


def test_every_declared_entry_point_names_a_target_the_scaffold_wrote(tmp_path: Path):
    """The honouring, not only the shape: an entry point pointing at a module the
    scaffold never wrote is a package that fails to load on install, and a test
    asserting only the table's keys would pass on exactly that."""
    root = scaffold_plugin(tmp_path / "publishable-my-assay")
    declared = tomllib.loads((root / "pyproject.toml").read_text())
    for group, entries in declared["project"]["entry-points"].items():
        for key, target in entries.items():
            module, _, attribute = target.partition(":")
            path = root / "src" / Path(*module.split(".")).with_suffix(".py")
            assert path.is_file(), f"{group} {key} points at {module}, which is not written"
            assert attribute in path.read_text()


def test_each_decorator_is_applied_under_the_key_the_entry_point_declares(tmp_path: Path):
    """`reference.md` § Creating a plugin: the entry point is the registration and
    the decorator is a declaration checked against it. A scaffold whose two halves
    disagreed would ship a package `check_registration` refuses on first load —
    which is exactly the drift that check exists to catch, shipped by core."""
    root = scaffold_plugin(tmp_path / "publishable-my-assay")
    declared = tomllib.loads((root / "pyproject.toml").read_text())
    for group, entries in declared["project"]["entry-points"].items():
        decorator = "register_" + group.rsplit(".", 1)[1].rstrip("s")
        for key, target in entries.items():
            module = target.partition(":")[0]
            source = (root / "src" / Path(*module.split(".")).with_suffix(".py")).read_text()
            assert f'@{decorator}("{key}")' in source


def test_the_package_name_is_the_distribution_name_with_hyphens_turned_over(tmp_path: Path):
    assert package_name("publishable-my-assay") == "publishable_my_assay"
    root = scaffold_plugin(tmp_path / "publishable-my-assay")
    assert (root / "src" / "publishable_my_assay" / "__init__.py").is_file()


def test_a_non_empty_directory_is_refused(tmp_path: Path):
    """Greenfield, `scaffold_project`'s rule and its code: a plugin's `src/**` is
    code a run's numbers come out of once it is installed."""
    root = tmp_path / "publishable-my-assay"
    root.mkdir()
    (root / "keepme.txt").write_text("mine\n")
    with pytest.raises(ContractError) as excinfo:
        scaffold_plugin(root)
    assert excinfo.value.code == "E-PROJECT-EXISTS"
    assert (root / "keepme.txt").read_text() == "mine\n"  # nothing was overwritten
