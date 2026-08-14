import sys
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


def _modules_under(directory: Path) -> list[str]:
    """Every `sys.modules` key whose module was loaded out of `directory`.

    Computed rather than enumerated by name. Listing the two helper names by
    hand would pass a defect that evicted `plain` but left `plain.data`, and
    `import plain.data` consults `sys.modules["plain.data"]` first — so a stale
    submodule is a leak on its own, and one no hand-written list would have
    thought to include.
    """
    root = directory.resolve()

    def under(candidate: str) -> bool:
        here = Path(candidate).resolve()
        return root == here or root in here.parents

    leaked = []
    for key, module in list(sys.modules.items()):
        origin = getattr(module, "__file__", None)
        paths = list(getattr(module, "__path__", ()))
        if (origin and under(origin)) or any(under(entry) for entry in paths):
            leaked.append(key)
    return sorted(leaked)


def _two_repos_each_holding_my_assay(tmp_path: Path) -> tuple[Path, Path]:
    """Repo A and repo B, both with `templates/my_assay.py` registering `my_assay`.

    Each file imports helpers from its own `templates/`, in both shapes a
    helper directory comes in — `support/` with an `__init__.py`, and `plain/`
    without one, which Python makes a *namespace* package with no `__file__` at
    all. Both, because a restore that tested only `__file__` would leave the
    namespace package cached and leak it to the next repo; and directories
    rather than sibling `.py` files, because every `templates/*.py` is itself
    imported by discovery, so a sibling would be re-imported per repo by
    accident and no leak would show.

    `plain.data` carries a `__file__` and is evicted either way, so the value
    it holds is not what the namespace package costs. What it costs is the
    *parent* surviving in `sys.modules` with the previous repo's submodules
    still attached to it — which a file saying `import plain` and reading
    `plain.data` is then handed, silently and with the wrong repo's data. That
    file cannot be written as a fixture here, because once the residue is gone
    it is an `AttributeError` rather than a value; the residue's absence is
    asserted directly instead.
    """
    roots = []
    for tag in ("a", "b"):
        root = tmp_path / tag
        (root / "templates" / "support").mkdir(parents=True)
        (root / "templates" / "plain").mkdir(parents=True)
        (root / "templates" / "support" / "__init__.py").write_text(f'ORIGIN = "{tag.upper()}"\n')
        (root / "templates" / "plain" / "data.py").write_text(f'ORIGIN = "{tag.upper()}"\n')
        (root / "templates" / "my_assay.py").write_text(
            "import support\n"
            "import plain.data\n"
            "from publishable import BaseTemplate, register_template\n\n\n"
            '@register_template("my_assay")\n'
            "class MyAssay(BaseTemplate):\n"
            f'    """{tag.upper()}\'s"""\n\n'
            "    origin = support.ORIGIN\n"
            "    namespaced_origin = plain.data.ORIGIN\n"
        )
        roots.append(root)
    return roots[0], roots[1]


def test_two_repos_in_one_process_do_not_cross_contaminate(tmp_path: Path):
    """Both repos hold `templates/my_assay.py`, registering the same name but
    different classes. Resolving from repo A then repo B must give B's class —
    asserted by class identity (`__doc__`, and `origin` carried from the repo's
    own helper), never by the name, which is identical either way and so proves
    nothing.

    Three claims, each dying to a different defect:

    - `origin` — repo B's `import support` served repo A's package from
      `sys.modules`, so B's class silently carries A's data. This is the one
      that fails today, and it dies to dropping the `sys.modules` restore.
    - no `plain` or `support` left in `sys.modules` — the restore must catch a
      helper directory with no `__init__.py` too, which has no `__file__` to
      test. Dies to a restore that looks at `__file__` alone.
    - `__module__` inequality — the two files are not one `sys.modules` entry.
      Dies to keying the synthetic module name on the file stem alone.

    `namespaced_origin` is a control rather than a claim: it holds under every
    one of those defects, and it is here so a fix that made the namespace
    helper unimportable fails rather than passing the residue assertion."""
    repo_a, repo_b = _two_repos_each_holding_my_assay(tmp_path)

    a = get_template("my_assay", repo_a)
    b = get_template("my_assay", repo_b)

    assert a is not None and b is not None
    assert type(a).__doc__ == "A's"
    assert type(b).__doc__ == "B's"
    assert type(a).origin == "A"
    assert type(b).origin == "B"
    assert type(a).namespaced_origin == "A"
    assert type(b).namespaced_origin == "B"
    assert type(a) is not type(b)
    assert type(a).__module__ != type(b).__module__
    assert _modules_under(tmp_path) == []


def test_a_repos_own_templates_are_reachable_from_a_second_call(tmp_path: Path):
    """THE CONTROL for the test above: naming a module per repo must not make a
    repo resolvable only once. Nothing is cached, so the same root asked twice
    re-imports and answers identically — with the same class *identity*, since
    two separate imports of one file give two unequal classes."""
    repo_a, _ = _two_repos_each_holding_my_assay(tmp_path)

    first = get_template("my_assay", repo_a)
    second = get_template("my_assay", repo_a)

    assert first is not None and second is not None
    assert type(first).__doc__ == type(second).__doc__ == "A's"
    assert type(first).origin == type(second).origin == "A"


def test_a_template_that_mutates_sys_path_does_not_leak_to_the_next_repo(tmp_path: Path):
    """A template whose top level touches `sys.path` — itself, or through any
    library it imports — must not move the entry discovery is about to take
    back off. Taking it by the index captured before the import deletes an
    unrelated entry instead (`.../publishable/src`, measured) and leaves this
    repo's `templates/` on `sys.path` for good, which is how repo B ends up
    served repo A's helper: `origin` is the assertion that catches that, and
    `sys.path` being unchanged is the assertion that catches the entry lost on
    the way.

    A `remove` of the string is no better and fails the other way round, which
    is why each template here appends its *own* directory as well: `remove`
    takes the first occurrence, which is discovery's, and leaves the
    template's copy behind — same permanent entry, same leak. Only putting
    `sys.path` back whole survives both."""
    for tag in ("a", "b"):
        templates = tmp_path / tag / "templates"
        templates.mkdir(parents=True)
        (templates / "helperx.py").write_text(f'ORIGIN = "{tag.upper()}"\n')
        (templates / "my_assay.py").write_text(
            "import os\n"
            "import sys\n"
            "sys.path.insert(0, '/zzz')\n"
            "sys.path.append(os.path.dirname(__file__))\n"
            "import helperx\n"
            "from publishable import BaseTemplate, register_template\n\n\n"
            '@register_template("my_assay")\n'
            "class MyAssay(BaseTemplate):\n"
            "    origin = helperx.ORIGIN\n"
        )
    before = list(sys.path)

    a = get_template("my_assay", tmp_path / "a")
    b = get_template("my_assay", tmp_path / "b")

    assert a is not None and b is not None
    assert type(a).origin == "A"
    assert type(b).origin == "B"
    assert sys.path == before
    assert _modules_under(tmp_path) == []


def test_a_template_named_for_a_stdlib_module_does_not_import_itself(tmp_path: Path):
    """`templates/json.py` whose own top level says `import json`. Bound as
    `json` in `sys.modules` it gets *itself* back — deterministically, on every
    call, single-threaded — and the stdlib `json` is evicted from the process
    for good afterwards. `publishable` itself imports `io`, so `templates/io.py`
    carries the same hazard; it is named here rather than tested, because
    clobbering `sys.modules["io"]` mid-suite is worse than the bug.

    THE CONTROL is `saw_stdlib_json`: a fix that merely skipped files named
    after a stdlib module would leave the template unresolved and fail it."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "json.py").write_text(
        "import json\n"
        "from publishable import BaseTemplate, register_template\n\n\n"
        '@register_template("jsonish")\n'
        "class Jsonish(BaseTemplate):\n"
        "    saw_stdlib_json = hasattr(json, 'loads')\n"
    )

    resolved = get_template("jsonish", tmp_path)

    assert resolved is not None
    assert type(resolved).__name__ == "Jsonish"
    assert type(resolved).saw_stdlib_json is True
    assert hasattr(sys.modules["json"], "loads")


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
