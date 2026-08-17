# tests/test_plugins.py
import importlib
import sys

import pytest

from publishable.plugins import GROUPS, names, provider_of, scan_group


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


def test_the_scan_imports_nothing(installed):
    """The whole argument for entry points, asserted rather than described.

    The target is a module that **does** import, and the assertion is that it is
    absent from `sys.modules` after the scan. That is the only shape that
    catches a load: against a target that cannot import, a scan calling
    `.load()` inside a bare `except` returns normally and every assertion still
    holds — verified by mutation, which is how this test was rewritten. The
    trailing `.load()` is the positive control: the same object does resolve,
    and resolving it is exactly what puts the module in `sys.modules`, so the
    absence above is a fact about the scan rather than about the fixture.
    """
    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "loadable_probe:resolve"}}
    )
    (site / "loadable_probe.py").write_text("def resolve():\n    return []\n")
    importlib.invalidate_caches()
    assert "loadable_probe" not in sys.modules

    found = scan_group("publishable.resolvers")
    assert provider_of(found["plate_wells"][0]) == "dist-one 1.0"
    assert "loadable_probe" not in sys.modules

    try:
        assert found["plate_wells"][0].load()() == []
        assert "loadable_probe" in sys.modules
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
