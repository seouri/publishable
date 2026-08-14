from pathlib import Path

from publishable import BaseTemplate, Param
from publishable.stats import UnitTable
from publishable.templates.discovery import discover_local
from publishable.templates.registry import get_template, template_names


def test_generic_is_registered_and_declares_its_conventions():
    t = get_template("generic")
    assert isinstance(t, BaseTemplate)
    assert t.field_convention == "generic"
    assert t.default_repeats == 1
    assert t.required_env == []
    assert t.apparatus_probe is None


def test_generic_declares_exactly_its_four_parameters():
    spec = get_template("generic").parameter_spec
    assert list(spec) == [
        "analysis.method",
        "analysis.min_samples",
        "analysis.confidence",
        "analysis.drop_missing",
    ]
    assert spec["analysis.method"].choices == ["pearson", "spearman", "kendall"]
    assert spec["analysis.min_samples"].ge == 2


def test_an_unknown_template_is_not_resolved():
    assert get_template("llm_diagnostic") is None


def test_a_local_template_resolves_by_name(tmp_path: Path):
    """The headline. THE CONTROL: `generic` still resolves from the same call,
    so a change that replaced builtins with locals fails here."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "my_assay.py").write_text(
        "from publishable import BaseTemplate, register_template\n\n\n"
        '@register_template("my_assay")\n'
        "class MyAssay(BaseTemplate):\n"
        "    pass\n"
    )

    resolved = get_template("my_assay", tmp_path)
    assert resolved is not None
    assert type(resolved).__name__ == "MyAssay"
    assert get_template("generic", tmp_path) is not None


def test_without_a_repo_root_only_builtins_resolve(tmp_path: Path):
    """No root -> local discovery is skipped, `generic` still resolves. This is
    the behaviour task 4's hoist depends on. The local file genuinely exists on
    disk so this is a claim about the root argument, not about the file being
    absent."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "my_assay.py").write_text(
        "from publishable import BaseTemplate, register_template\n\n\n"
        '@register_template("my_assay")\n'
        "class MyAssay(BaseTemplate):\n"
        "    pass\n"
    )

    assert get_template("my_assay") is None
    assert get_template("generic") is not None


def test_a_repo_root_does_not_fabricate_an_unknown_name(tmp_path: Path):
    """`get_template("llm_diagnostic") is None` used to assert the closed set by
    name; with a repo root that is no longer a statement about the world, since
    a project could define it locally. What survives: a repo root does not
    invent names it was never given. THE CONTROL: a real local template
    (`real_one`) resolves from the same call, so a discovery that silently
    returned {} for everything would fail here rather than passing both
    assertions."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "real.py").write_text(
        "from publishable import BaseTemplate, register_template\n\n\n"
        '@register_template("real_one")\n'
        "class RealOne(BaseTemplate):\n"
        "    pass\n"
    )

    assert get_template("llm_diagnostic", tmp_path) is None
    assert get_template("real_one", tmp_path) is not None


def test_template_names_includes_locals_and_stays_sorted(tmp_path: Path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "my_assay.py").write_text(
        "from publishable import BaseTemplate, register_template\n\n\n"
        '@register_template("my_assay")\n'
        "class MyAssay(BaseTemplate):\n"
        "    pass\n"
    )

    assert template_names(tmp_path) == ["generic", "my_assay"]
    assert template_names() == ["generic"]


def test_per_call_merge_does_not_leak_between_two_roots(tmp_path: Path):
    """Two projects in one process must never see each other's `templates/` —
    a module-global merged mapping would leak `alpha` from `root_a` into the
    call for `root_b`. This is the dimension none of the tests above can see:
    each of them uses at most one root per test."""
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    (root_a / "templates").mkdir(parents=True)
    (root_b / "templates").mkdir(parents=True)
    (root_a / "templates" / "alpha.py").write_text(
        "from publishable import BaseTemplate, register_template\n\n\n"
        '@register_template("alpha")\n'
        "class Alpha(BaseTemplate):\n"
        "    pass\n"
    )

    assert get_template("alpha", root_a) is not None
    assert get_template("alpha", root_b) is None


def test_validate_defaults_to_no_cross_field_rules():
    class Bare(BaseTemplate):
        parameter_spec: dict[str, Param] = {}

    assert Bare().validate(None) == []


def test_the_base_aggregate_returns_nothing():
    """`{}` is the right answer for a table a template doesn't recognize — core
    calls `aggregate` once per recording step, and a pipeline can have several."""
    assert BaseTemplate().aggregate(UnitTable({"u1": {"pred": 1.0}}), None) == {}


def test_a_subclass_can_derive_from_the_table():
    class T(BaseTemplate):
        def aggregate(self, units, cfg):
            return {"total": sum(units.pred)}

    assert T().aggregate(UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}}), None) == {
        "total": 3.0
    }


def test_register_template_returns_the_class_and_records_the_name():
    """§ Creating a plugin: a local template's `@register_template` argument
    "is therefore the whole of its registration". The decorator must return the
    class unchanged — a decorator that returned the registration record would
    break `class X(BaseTemplate)` for every later reference to X."""
    from publishable import register_template
    from publishable.templates.discovery import drain_pending

    @register_template("my_assay")
    class MyAssay(BaseTemplate):
        pass

    assert MyAssay.__name__ == "MyAssay"          # returned unchanged
    assert issubclass(MyAssay, BaseTemplate)
    assert drain_pending() == [("my_assay", MyAssay)]
    assert drain_pending() == []                  # draining empties it


ALPHA_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("alpha")
class Alpha(BaseTemplate):
    pass
"""

BETA_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("beta")
class Beta(BaseTemplate):
    pass
"""

REAL_ONE_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("real_one")
class RealOne(BaseTemplate):
    pass
"""

DUNDER_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("should_not_be_found")
class ShouldNotBeFound(BaseTemplate):
    pass
"""


def test_discovery_imports_every_file_not_only_the_named_one(tmp_path: Path):
    """Two files, and the config names neither. Both must register, or a
    collision between them could not be detected — which is the whole reason
    discovery is eager rather than lazy."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "alpha.py").write_text(ALPHA_TEMPLATE)
    (templates / "beta.py").write_text(BETA_TEMPLATE)

    found = discover_local(tmp_path)

    assert sorted(found) == ["alpha", "beta"]
    assert found["alpha"].__name__ == "Alpha"
    assert found["beta"].__name__ == "Beta"
    assert issubclass(found["alpha"], BaseTemplate)
    assert issubclass(found["beta"], BaseTemplate)


def test_discovery_ignores_non_python_and_dunder_files(tmp_path: Path):
    """The scaffold puts `.gitkeep` in `templates/`. THE CONTROL: a real
    template beside it must still be found, so a discovery that returned {}
    for everything fails here rather than passing both assertions.

    `__init__.py` registers a name of its own here — an empty `__init__.py`
    would make the skip untestable, since importing it would register nothing
    either way, and `sorted(found) == ["real_one"]` would pass whether or not
    the skip existed.
    """
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / ".gitkeep").write_text("")
    (templates / "__init__.py").write_text(DUNDER_TEMPLATE)
    (templates / "notes.md").write_text("# not a template\n")
    (templates / "real.py").write_text(REAL_ONE_TEMPLATE)

    found = discover_local(tmp_path)

    assert sorted(found) == ["real_one"]
    assert found["real_one"].__name__ == "RealOne"


def test_discovery_with_no_templates_directory_is_empty_not_an_error(tmp_path: Path):
    assert discover_local(tmp_path) == {}


def test_discovery_leaves_no_stale_pending_registration_behind(tmp_path: Path):
    """A registration pending from before `discover_local` was called (a prior
    `@register_template` in the same process) must not leak into the result,
    and must not still be sitting in the buffer afterward — `discover_local`
    "returns what *they* [the files] registered", not what was already queued."""
    from publishable import register_template
    from publishable.templates.discovery import drain_pending

    @register_template("stale")
    class Stale(BaseTemplate):
        pass

    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "alpha.py").write_text(ALPHA_TEMPLATE)

    found = discover_local(tmp_path)

    assert sorted(found) == ["alpha"]
    assert drain_pending() == []
