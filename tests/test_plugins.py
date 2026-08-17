# tests/test_plugins.py
import importlib
import sys

import pytest

from publishable.plugins import (
    GROUPS,
    declared_names,
    load_entry_point,
    names,
    provider_of,
    scan_group,
)


def test_the_groups_core_reads_are_the_five_the_document_declares():
    """Named rather than counted: `reference.md` § Creating a plugin shows one
    `[project.entry-points."publishable.*"]` block per registry."""
    assert set(GROUPS) == {
        "publishable.templates",
        "publishable.resolvers",
        "publishable.probes",
        "publishable.writers",
        "publishable.readers",
    }


def test_an_absent_group_is_empty_and_a_present_one_is_not(installed):
    """The control and its positive companion in one test: an empty answer proves
    nothing on a machine where no plugin is installed, so the same call must
    return something once a distribution declares it."""
    assert scan_group("publishable.resolvers") == {}
    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "pkg_one.r:resolve"}})
    found = scan_group("publishable.resolvers")
    assert list(found) == ["plate_wells"]
    assert found["plate_wells"][0].value == "pkg_one.r:resolve"


def test_a_scan_selects_its_own_group_only(installed):
    installed(
        "dist-one",
        "1.0",
        {
            "publishable.resolvers": {"plate_wells": "pkg_one.r:resolve"},
            "publishable.probes": {"assay_instrument": "pkg_one.p:probe"},
            "console_scripts": {"whatever": "pkg_one.cli:main"},
        },
    )
    assert list(scan_group("publishable.resolvers")) == ["plate_wells"]
    assert list(scan_group("publishable.probes")) == ["assay_instrument"]
    assert scan_group("publishable.writers") == {}


def test_two_distributions_claiming_one_name_both_arrive(installed):
    """The metadata scan reports every claimant; deciding between them is the
    collision check's job and not this function's. Two distributions, because one
    cannot produce this arrangement at all.

    The fixture is arranged so that the asserted list distinguishes provider
    order from the two orderings it must rule out, neither of which a smaller
    one separates. `dist-one` is installed **first**, so `syspath_prepend` puts
    `dist-two` at `sys.path[0]` and the walk order is `dist-two, dist-one` — the
    reverse of the assertion, so dropping the sort fails here. And `dist-one`'s
    target sorts **after** `dist-two`'s (`pkg_zeta` > `pkg_alpha`) while its
    provider sorts before, so sorting by `ep.value` instead of by provider also
    fails here. Both were verified by mutation; with the values tracking the
    distribution names, as they first did, neither ordering was pinned at all.
    """
    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "pkg_zeta.r:resolve"}})
    installed("dist-two", "2.0", {"publishable.resolvers": {"plate_wells": "pkg_alpha.r:resolve"}})
    providers = [provider_of(ep) for ep in scan_group("publishable.resolvers")["plate_wells"]]
    assert providers == ["dist-one 1.0", "dist-two 2.0"]


def test_names_are_sorted_and_the_sort_is_not_the_install_order(installed):
    """`zz_first` is installed first and sorts last; `aa_second` is installed
    second and sorts first. Two names in one arrangement cannot tell sorted order
    from insertion order — with two, the reverse of insertion IS sorted for one
    arrangement — so three names are declared and their install order is neither
    sorted nor reverse-sorted.
    """
    installed(
        "dist-order",
        "1.0",
        {
            "publishable.resolvers": {
                "zz_first": "pkg.r:a",
                "aa_second": "pkg.r:b",
                "mm_third": "pkg.r:c",
            }
        },
    )
    assert names("publishable.resolvers") == ["aa_second", "mm_third", "zz_first"]


def test_the_scan_imports_nothing(installed, registries):
    """The whole argument for entry points, asserted rather than described, and
    narrowed to the claim that is actually true.

    **A NAME resolves from package metadata without importing** — that is
    § Creating a plugin's guarantee and the whole of it. `validate` does import a
    plugin once it needs the object behind a name: a resolver runs at `validate`,
    which is § Where units come from's design.

    The target is a module that **does** import, and the assertion is that it is
    absent from `sys.modules` after every name-answering call. That is the only
    shape that catches a load: against a target that cannot import, a scan calling
    `.load()` inside a bare `except` returns normally and every assertion still
    holds. `load_entry_point` is the positive control and is the production import
    path rather than a bare `.load()`, so this test states the boundary in the
    terms the code uses: everything that answers a name imports nothing;
    `load_entry_point` imports, by name.
    """
    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "loadable_probe:resolve"}}
    )
    (site / "loadable_probe.py").write_text(
        "from publishable import register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n    return []\n"
    )
    importlib.invalidate_caches()
    assert "loadable_probe" not in sys.modules

    found = scan_group("publishable.resolvers")
    assert provider_of(found["plate_wells"][0]) == "dist-one 1.0"
    assert "loadable_probe" not in sys.modules

    assert names("publishable.resolvers") == ["plate_wells"]
    assert "loadable_probe" not in sys.modules

    try:
        loaded = load_entry_point(found["plate_wells"][0])
        assert loaded(None, None) == []
        assert "loadable_probe" in sys.modules
        assert declared_names("publishable.resolvers", loaded) == ["plate_wells"]
    finally:
        sys.modules.pop("loadable_probe", None)


def test_register_resolver_records_the_name_and_returns_the_function(registries):
    """The decorator's two obligations. Returning the object unchanged is the
    half a decorator gets wrong silently: a `None` return leaves the plugin's own
    module holding `None` under the name it just defined, and its own test suite
    is where that surfaces."""
    from publishable.plugins import RESOLVERS, register_resolver

    @register_resolver("plate_wells")
    def resolve(io, cfg):
        return ["a unit"]

    assert RESOLVERS["plate_wells"] is resolve
    assert resolve(None, None) == ["a unit"]  # still callable under its own name


def test_a_leaked_registration_would_be_visible_to_the_next_test(registries):
    """Pins the `registries` fixture's restore loop itself. A fixture that
    snapshots but never restores looks identical to a working one to every
    other test in this module, because none of them checks state left behind
    by a *previous* test — so this one plants a registration and the test
    immediately below, which runs next in this file's declaration order,
    checks it is gone. If the restore loop were replaced with a no-op, this
    test would still pass (it only registers) and the one below would go red."""
    from publishable.plugins import register_resolver

    @register_resolver("_registries_fixture_leak_probe")
    def resolve(io, cfg):
        return []


def test_the_previous_test_s_registration_did_not_leak(registries):
    """Companion to the test immediately above — see its docstring. Also uses
    `registries` itself, so a failure here means the *previous* test's
    teardown didn't run, not this test's own setup."""
    from publishable.plugins import RESOLVERS

    assert "_registries_fixture_leak_probe" not in RESOLVERS


def test_a_resolver_is_importable_from_the_one_root():
    """`reference.md` § The importable surface: everything you write against is
    imported from `publishable` itself. A plugin importing
    `publishable.plugins.register_resolver` is not a supported spelling even
    where it works."""
    import publishable

    assert "register_resolver" in publishable.__all__
    assert publishable.register_resolver is not None


def test_register_probe_records_the_name_and_returns_the_function(registries):
    from publishable.plugins import PROBES, register_probe

    @register_probe("assay_instrument")
    def probe(cfg):
        return {"model": "x"}

    assert PROBES["assay_instrument"] is probe
    assert probe(None) == {"model": "x"}


def test_a_probe_is_importable_from_the_one_root():
    """`reference.md` § The importable surface: everything you write against is
    imported from `publishable` itself. Asserting `__all__` membership alone
    cannot catch a dropped export — the import line above it can still fail
    while `__all__` stays untouched — so this must import the name itself."""
    import publishable

    assert "register_probe" in publishable.__all__
    assert publishable.register_probe is not None


def test_a_writer_is_importable_from_the_one_root():
    """Same shape as the resolver and probe checks above: `__all__` membership
    alone cannot catch a dropped export from `publishable/__init__.py`."""
    import publishable

    assert "register_writer" in publishable.__all__
    assert publishable.register_writer is not None


def test_a_reader_is_importable_from_the_one_root():
    """Same shape as the resolver and probe checks above: `__all__` membership
    alone cannot catch a dropped export from `publishable/__init__.py`."""
    import publishable

    assert "register_reader" in publishable.__all__
    assert publishable.register_reader is not None


def test_a_third_party_suffix_reaches_io_write_s_dispatch(registries, tmp_path):
    """Registration is only real if `io.write` finds it, so the assertion is over
    the dispatch rather than over the dict — `_suffix_for` is what decides, and
    it iterates `WRITERS`.

    `.gz` is registered *before* `.fastq.gz` on purpose: registering the
    longer suffix first would leave "longest wins" and "first-registered
    wins" agreeing on the answer, since the longer one would also be first.
    Registering the shorter one first is what makes the two readings diverge
    — only "longest wins" gets `.fastq.gz` for `sample.fastq.gz`."""
    from publishable import artifacts
    from publishable.plugins import register_writer

    @register_writer(".gz")
    def write_gz(rows):
        return b""

    assert artifacts._suffix_for("sample.fastq.gz") == ".gz"

    # The longest registered suffix still wins, which is what a compound
    # extension is registered for: `.gz` alone must not claim this name,
    # even though it was registered first.
    @register_writer(".fastq.gz")
    def write_fastq(rows):
        return b"@read\n"

    assert artifacts._suffix_for("sample.fastq.gz") == ".fastq.gz"
    assert artifacts.WRITERS[".fastq.gz"] is write_fastq


def test_a_plugin_writer_is_reached_through_the_public_io_write(registries, tmp_path):
    """The test above stops at `_suffix_for` and `WRITERS[...] is write_fn` — one
    call frame short of `io.write` itself, which is what a step actually calls.
    `StepIO.write` calls `WRITERS[suffix](obj)` and then writes the returned
    bytes, so this drives a plugin suffix through that public method and reads
    the bytes back off disk, rather than asserting on the private dispatch."""
    from publishable.artifacts import StepIO
    from publishable.plugins import register_writer

    @register_writer(".fastq")
    def write_fastq(rows):
        return "|".join(rows).encode()

    step_dir = tmp_path / "run" / "step"
    step_dir.mkdir(parents=True)
    (tmp_path / "input").mkdir()
    io = StepIO(step_dir=step_dir, input_dir=tmp_path / "input", run_dir=tmp_path / "run")

    path = io.write("out.fastq", ["a", "b"])
    assert path.read_bytes() == b"a|b"


def test_a_writer_may_not_claim_a_suffix_core_writes(registries):
    """A plugin that could redefine `.csv` could change what an artifact means
    without changing the step that wrote it."""
    from publishable.errors import ContractError
    from publishable.plugins import register_writer

    with pytest.raises(ContractError) as excinfo:

        @register_writer(".csv")
        def write_csv(rows):
            return b""

    assert excinfo.value.code == "E-PLUGIN-COLLISION"
    message = str(excinfo.value)
    assert ".csv" in message
    assert "core" in message


def test_a_suffix_core_does_not_write_is_accepted(registries):
    """THE CONTROL, and the honouring: a refusal that fired for every suffix
    would pass the test above. Paired here rather than left implicit."""
    from publishable import artifacts
    from publishable.plugins import register_writer

    @register_writer(".fastq")
    def write_fastq(rows):
        return b""

    assert ".fastq" in artifacts.WRITERS

    # A second plugin claiming the SAME suffix is not this check's refusal — it
    # is decided from entry-point metadata, where both claimants are visible.
    # Registering twice in one process is what a plugin's own test suite does,
    # and refusing it here would refuse that.
    @register_writer(".fastq")
    def write_fastq_again(rows):
        return b""

    assert artifacts.WRITERS[".fastq"] is write_fastq_again


def test_register_reader_completes_the_pair_io_read_upstream_needs(registries, tmp_path):
    """Registering both halves is what a plugin does, and the pair is what makes
    the round trip real — asserted as a round trip rather than as two dict
    entries, since two entries is what the broken state also looks like."""
    from publishable import artifacts
    from publishable.plugins import register_reader, register_writer

    @register_writer(".fastq")
    def write_fastq(rows):
        return "|".join(rows).encode()

    @register_reader(".fastq")
    def read_fastq(data):
        return data.decode().split("|")

    target = tmp_path / "a.fastq"
    target.write_bytes(artifacts.WRITERS[".fastq"](["a", "b"]))
    assert artifacts.StepIO._read(target) == ["a", "b"]


def test_a_reader_may_not_claim_a_suffix_core_reads(registries):
    from publishable.errors import ContractError
    from publishable.plugins import register_reader

    with pytest.raises(ContractError) as excinfo:

        @register_reader(".csv")
        def read_csv(data):
            return []

    assert excinfo.value.code == "E-PLUGIN-COLLISION"


def test_a_decorator_argument_matching_its_key_is_accepted(registries):
    """The honouring. Without it, a check that raised unconditionally passes
    every refusal below."""
    from importlib.metadata import EntryPoint

    from publishable.plugins import check_registration, declared_names, register_resolver

    @register_resolver("plate_wells")
    def resolve(io, cfg):
        return []

    ep = EntryPoint(name="plate_wells", value="pkg.r:resolve", group="publishable.resolvers")
    assert declared_names("publishable.resolvers", resolve) == ["plate_wells"]
    check_registration(ep, declared_names("publishable.resolvers", resolve))


def test_a_decorator_argument_disagreeing_with_its_key_is_refused(registries):
    """Two spellings of one name with no rule for which is canonical is a drift
    nobody detects until a config names the loser — the defaults-file argument."""
    from importlib.metadata import EntryPoint

    from publishable.errors import ContractError
    from publishable.plugins import check_registration, declared_names, register_resolver

    @register_resolver("plate_positions")
    def resolve(io, cfg):
        return []

    ep = EntryPoint(name="plate_wells", value="pkg.r:resolve", group="publishable.resolvers")
    with pytest.raises(ContractError) as excinfo:
        check_registration(ep, declared_names("publishable.resolvers", resolve))

    assert excinfo.value.code == "E-PLUGIN-DECORATOR"
    message = str(excinfo.value)
    assert "plate_wells" in message  # the key
    assert "plate_positions" in message  # the decorator argument
    assert "pkg.r:resolve" in message  # where to look


def test_an_object_registered_under_several_names_satisfies_any_of_them(registries):
    """One function may serve two keys — a plugin registering the same resolver
    under an old name and a new one is not a disagreement. The check is
    membership, not equality, and a fixture with one name could not tell the two
    readings apart."""
    from importlib.metadata import EntryPoint

    from publishable.plugins import check_registration, declared_names, register_resolver

    def resolve(io, cfg):
        return []

    register_resolver("plate_wells")(resolve)
    register_resolver("plate_positions")(resolve)

    for key in ("plate_wells", "plate_positions"):
        ep = EntryPoint(name=key, value="pkg.r:resolve", group="publishable.resolvers")
        check_registration(ep, declared_names("publishable.resolvers", resolve))


def test_an_object_that_registered_nothing_is_refused_and_says_so(registries):
    """The distinguishable branch: "declared a different name" and "declared no
    name at all" are different mistakes with different remedies, so their
    messages must differ. Pinned separately, because both carry one code."""
    from importlib.metadata import EntryPoint

    from publishable.errors import ContractError
    from publishable.plugins import check_registration

    ep = EntryPoint(name="plate_wells", value="pkg.r:resolve", group="publishable.resolvers")
    with pytest.raises(ContractError) as excinfo:
        check_registration(ep, [])

    message = str(excinfo.value)
    assert "calls no `@register_" in message  # only this branch says this
    assert "declares `" not in message  # and only the other branch says that


def test_a_plugin_module_that_raises_is_a_coded_refusal_naming_the_distribution(installed):
    """A traceback out of a command is the outcome core is contracted never to
    produce. The distribution is named rather than the module, because a
    distribution is what a reader uninstalls or pins."""
    from publishable.errors import ContractError
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "boom_module:resolve"}}
    )
    (site / "boom_module.py").write_text("raise RuntimeError('kaboom')\n")

    ep = scan_group("publishable.resolvers")["plate_wells"][0]
    with pytest.raises(ContractError) as excinfo:
        load_entry_point(ep)

    assert excinfo.value.code == "E-PLUGIN-LOAD"
    message = str(excinfo.value)
    assert "plate_wells" in message
    assert "dist-one 1.0" in message
    assert "RuntimeError" in message


def test_a_stale_pending_registration_is_not_inherited_onto_this_load(installed):
    """`load_entry_point`'s docstring claims "a registration this import made is
    not the next one's to inherit" — which also means the reverse: a
    registration queued by something *earlier*, and never drained, is not this
    import's to inherit either.

    `cli` imports the experiment package before `validate_config` runs, so a
    stray module-scope `@register_template` elsewhere in the process is exactly
    the kind of entry that can sit in the pending buffer when `load_entry_point`
    is called. Without a pre-drain, `boom_module`'s refusal would carry a class
    it never touched.
    """
    from publishable import BaseTemplate
    from publishable.errors import ContractError
    from publishable.plugins import load_entry_point, scan_group
    from publishable.templates.discovery import _pending

    class Stale(BaseTemplate):
        required_env = ["STALE_KEY"]

    _pending.append(("stale", Stale))
    try:
        site = installed(
            "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "boom_module:resolve"}}
        )
        (site / "boom_module.py").write_text("raise RuntimeError('kaboom')\n")

        ep = scan_group("publishable.resolvers")["plate_wells"][0]
        with pytest.raises(ContractError) as excinfo:
            load_entry_point(ep)
    finally:
        _pending.clear()

    carried = getattr(excinfo.value, "partial_templates", None)
    assert carried == []


def test_a_plugin_module_calling_sys_exit_is_contained_too(installed):
    """`SystemExit` is a `BaseException`, so the broad arm does not see it — the
    mutation for this is deleting the `except SystemExit` and watching pytest
    exit rather than report."""
    from publishable.errors import ContractError
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "exiting_module:resolve"}}
    )
    (site / "exiting_module.py").write_text("import sys\nsys.exit(3)\n")

    ep = scan_group("publishable.resolvers")["plate_wells"][0]
    with pytest.raises(ContractError) as excinfo:
        load_entry_point(ep)

    assert excinfo.value.code == "E-PLUGIN-LOAD"
    assert "SystemExit: 3" in str(excinfo.value)


def test_a_class_a_failing_plugin_declared_before_raising_is_carried(installed):
    """The widened pattern. A class body finishes running before its own
    decorator is reached, so a module that raises AFTER registering still leaves
    a fully formed class — carried on the refusal so a caller that never gets a
    usable object can still read what it declared.
    """
    from publishable.plugins import load_entry_point, scan_group

    site = installed("dist-one", "1.0", {"publishable.templates": {"my_assay": "half_module:T"}})
    (site / "half_module.py").write_text(
        "from publishable import BaseTemplate, register_template\n"
        "\n"
        "\n"
        "@register_template('my_assay')\n"
        "class T(BaseTemplate):\n"
        "    required_env = ['SOME_KEY']\n"
        "\n"
        "\n"
        "raise RuntimeError('after registering')\n"
    )

    ep = scan_group("publishable.templates")["my_assay"][0]
    with pytest.raises(Exception) as excinfo:
        load_entry_point(ep)

    carried = getattr(excinfo.value, "partial_templates", None)
    assert carried is not None
    assert [cls.required_env for cls in carried] == [["SOME_KEY"]]


def test_a_plugin_module_that_imports_cleanly_hands_back_its_object(installed):
    """THE HONOURING. Every test above asserts a refusal; without this one a
    `load_entry_point` that raised unconditionally would pass all three."""
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "good_module:resolve"}}
    )
    (site / "good_module.py").write_text("def resolve(io, cfg):\n    return ['a unit']\n")

    ep = scan_group("publishable.resolvers")["plate_wells"][0]
    assert load_entry_point(ep)(None, None) == ["a unit"]
