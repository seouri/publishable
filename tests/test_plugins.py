# tests/test_plugins.py
import importlib
import sys

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
    import publishable

    assert "register_probe" in publishable.__all__
