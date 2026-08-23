from pathlib import Path

from publishable.hashes import (
    code_hash,
    code_hash_of,
    covered_config,
    design_digest,
    hashed_files,
    parameters_hash,
    short,
)


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_code_hash_covers_src_and_templates_only(tmp_path: Path):
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    write(tmp_path, "templates/mine.py", "b = 2\n")
    before = code_hash(tmp_path, None)
    write(tmp_path, "docs/notes.md", "unrelated\n")
    write(tmp_path, "configs/c/config.yaml", "x: 1\n")
    assert code_hash(tmp_path, None) == before, "changes outside the two trees must not move it"
    write(tmp_path, "src/pkg/step.py", "a = 2\n")
    assert code_hash(tmp_path, None) != before


def test_code_hash_is_prefixed_and_short_takes_seven(tmp_path: Path):
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    h = code_hash(tmp_path, None)
    assert h.startswith("sha256:")
    assert len(short(h)) == 7


def test_code_hash_delegates_to_code_hash_of_over_hashed_files(tmp_path: Path):
    """H6a task 3, step 3. Two implementations of one fold is what
    `covered_config` was extracted to prevent (H8b task 7) — this is the same
    property for `code_hash`/`code_hash_of`/`hashed_files`, pinned as an
    identity rather than left to a docstring's claim.

    Asserted on a bare `include=None` tree AND on a tree with a real,
    non-trivial `include`, so the identity holds for both of `code_hash`'s
    two behaviours — hashing everything, and narrowing to a caller's filter.
    """
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    write(tmp_path, "src/pkg/other.py", "b = 2\n")
    write(tmp_path, "templates/t.py", "c = 3\n")
    assert code_hash(tmp_path, None) == code_hash_of(hashed_files(tmp_path, None))

    def drop_other(candidates: list[str]) -> set[str]:
        return {c for c in candidates if not c.endswith("other.py")}

    assert code_hash(tmp_path, drop_other) == code_hash_of(hashed_files(tmp_path, drop_other))
    # The filter actually narrowed something, or the second assertion would be
    # indistinguishable from the first.
    assert code_hash(tmp_path, drop_other) != code_hash(tmp_path, None)


def test_parameters_hash_excludes_metadata_and_the_two_paths():
    base = {
        "experiment_type": "generic",
        "metadata": {"name": "a", "description": "one"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
    }
    retitled = {**base, "metadata": {"name": "b", "description": "two"}}
    moved = {**base, "data": {**base["data"], "input_dir": "/elsewhere"}}
    changed = {**base, "parameters": {"analysis": {"method": "spearman"}}}
    assert parameters_hash(base) == parameters_hash(retitled)
    assert parameters_hash(base) == parameters_hash(moved)
    assert parameters_hash(base) != parameters_hash(changed)
    policy = {**base, "data": {**base["data"], "input_manifest_policy": "none"}}
    assert parameters_hash(base) != parameters_hash(policy), "policy is inside the hash"


def test_parameters_hash_is_insensitive_to_key_order():
    a = {"parameters": {"x": 1, "y": 2}, "limits": {"max_executions": 500}}
    b = {"limits": {"max_executions": 500}, "parameters": {"y": 2, "x": 1}}
    assert parameters_hash(a) == parameters_hash(b)


def test_code_hash_skip_list_matches_relative_path_not_absolute(tmp_path: Path):
    # A repo checked out beneath a directory literally named "__pycache__" must
    # not have its skip-list matched against components ABOVE repo_root — only
    # components inside src/**  or templates/** may be excluded.
    repo = tmp_path / "__pycache__" / "repo"
    write(repo, "src/pkg/step.py", "a = 1\n")
    empty_digest = code_hash(tmp_path / "nonexistent_empty_repo", None)
    h = code_hash(repo, None)
    assert h != empty_digest
    write(repo, "src/pkg/step.py", "a = 2\n")
    assert code_hash(repo, None) != h


def test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree(tmp_path: Path):
    """The fixed skip set drops `__pycache__` **unconditionally** — whatever
    git says about the files inside it.

    **This test absorbed a twin.** `test_code_hash_ignores_pycache` was
    byte-identical in body — same file, same `.pyc`, same assertion — so
    deleting either one alone left the suite green and one of the two was
    doing no work. What survives is the half that can fail for a reason the
    other could not: the tracked arm below asks git.

    `src/pkg/__pycache__/keep.py` is **tracked** (`git add -f`), and git
    reports it as **not excluded** — asserted here as `check-ignore`'s
    returncode 1, not assumed. The digest is unmoved all the same, which is
    what *unconditionally* means and what separates this test from guard-pin
    arm D's second tree: that arm calls `code_hash(..., None)`, so git is
    never asked at all, and a predicate applied before the fixed skip set
    would pass it.
    """
    import subprocess

    tree = _h6a_base_repo(tmp_path / "tree")
    (tree / "src" / "pkg" / "loose.pyd").write_text("X")
    _h6a_commit_more(tree, "src/pkg/loose.pyd")
    before = code_hash_of(hashed_files(tree, _h6a_include(tree)))
    assert before == "sha256:eec1541edde45c11c395e788000f719a48965a8f6fd2b3772a56de92cca18dc2"

    # The untracked half the removed twin held, kept: a real `.pyc` written by
    # the interpreter moves nothing.
    write(tree, "src/pkg/__pycache__/step.cpython-311.pyc", "junk")
    # The tracked half, which the twin could not hold at all.
    write(tree, "src/pkg/__pycache__/keep.py", "k = 1\n")
    _h6a_commit_more(tree, "src/pkg/__pycache__/keep.py")
    asked = subprocess.run(
        ["git", "check-ignore", "src/pkg/__pycache__/keep.py"], cwd=tree, capture_output=True
    )
    assert asked.returncode == 1, "git must report this tracked file as NOT excluded"

    assert code_hash_of(hashed_files(tree, _h6a_include(tree))) == before
    assert code_hash(tree, None) == before


def test_code_hash_handles_a_dot_git_intermediate_path_component(tmp_path: Path):
    repo = tmp_path / ".git" / "repo"
    write(repo, "src/pkg/step.py", "a = 1\n")
    empty_digest = code_hash(tmp_path / "nonexistent_empty_repo", None)
    assert code_hash(repo, None) != empty_digest


def test_parameters_hash_does_not_mutate_input():
    config = {
        "metadata": {"name": "a"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
    }
    before = {
        "metadata": {"name": "a"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
    }
    parameters_hash(config)
    assert config == before


def test_design_digest_covers_units_and_groups_only():
    base = {
        "data": {"units": {"key": "patient_id"}},
        "sweep": {"groups": [], "grid": {"analysis.method": ["spearman"]}},
        "parameters": {"analysis": {"min_samples": 30}},
    }
    edited = {**base, "parameters": {"analysis": {"min_samples": 50}}}
    assert design_digest(base) == design_digest(edited), "editing a parameter must not redraw"
    roster = {**base, "data": {"units": {"key": "sample_id"}}}
    assert design_digest(base) != design_digest(roster)


def _units_with_arm(seed=1, method="blocked", from_="site", stratify_by="age_band"):
    return {
        "data": {
            "units": {
                "key": "patient_id",
                "assign": {
                    "arm": {
                        "method": method,
                        "seed": seed,
                        "from": from_,
                        "stratify_by": stratify_by,
                    }
                },
            }
        },
    }


def test_design_digest_excludes_assign_seed_with_a_control():
    base = _units_with_arm(seed=1)
    reseeded = _units_with_arm(seed=2)
    assert design_digest(base) == design_digest(reseeded), "assign.seed must not move the digest"

    # Control: a different key must still move it, proving the exclusion is
    # not "the whole config is ignored".
    key_changed = {
        **base,
        "data": {**base["data"], "units": {**base["data"]["units"], "key": "sample_id"}},
    }
    assert design_digest(base) != design_digest(key_changed)


def test_design_digest_exclusion_is_surgical_not_the_whole_assign_block():
    base = _units_with_arm()

    from_changed = _units_with_arm(from_="clinic")
    assert design_digest(base) != design_digest(from_changed), (
        "assign.arm.from is a different partition and must move the digest"
    )

    stratify_changed = _units_with_arm(stratify_by="sex")
    assert design_digest(base) != design_digest(stratify_changed), (
        "assign.arm.stratify_by is a different balancing draw and must move the digest"
    )

    second_axis = {
        **base,
        "data": {
            **base["data"],
            "units": {
                **base["data"]["units"],
                "assign": {
                    **base["data"]["units"]["assign"],
                    "sex": {"method": "blocked", "seed": 5},
                },
            },
        },
    }
    assert design_digest(base) != design_digest(second_axis), (
        "adding a second axis to assign must move the digest"
    )


def test_design_digest_exclusion_is_per_axis_not_first_found():
    two_axes = {
        "data": {
            "units": {
                "key": "patient_id",
                "assign": {
                    "arm": {"method": "blocked", "seed": 1, "from": "site"},
                    "sex": {"method": "blocked", "seed": 5},
                },
            }
        },
    }
    reseeded_second_axis = {
        "data": {
            "units": {
                "key": "patient_id",
                "assign": {
                    "arm": {"method": "blocked", "seed": 1, "from": "site"},
                    "sex": {"method": "blocked", "seed": 99},
                },
            }
        },
    }
    assert design_digest(two_axes) == design_digest(reseeded_second_axis), (
        "the second axis's own seed must be excluded too, not just the first axis found"
    )


def test_design_digest_does_not_raise_on_malformed_assign_shapes():
    non_mapping_assign = {"data": {"units": {"key": "patient_id", "assign": "not-a-mapping"}}}
    non_mapping_block = {
        "data": {"units": {"key": "patient_id", "assign": {"arm": "not-a-mapping"}}}
    }
    non_mapping_units = {"data": {"units": "not-a-mapping"}}
    none_seed = {
        "data": {
            "units": {
                "key": "patient_id",
                "assign": {"arm": {"seed": None, "method": "blocked"}},
            }
        }
    }
    for config in (non_mapping_assign, non_mapping_block, non_mapping_units, none_seed):
        design_digest(config)  # must not raise


def test_a_pinned_holdout_seed_does_not_move_the_design_digest():
    """A seed that is itself inside the digest it is mixed with makes the
    derivation self-referential — and worse, moves every OTHER derived draw in
    the run. `assign.<axis>.seed` is already excluded for that reason; this is
    the same exclusion one field over.

    The positive companion is in the same test: changing a NON-seed holdout
    field MUST move the digest, or an implementation that dropped the whole
    `holdout` block would pass the first assertion alone."""
    base = {
        "data": {
            "units": {
                "from": "index.csv",
                "key": "patient_id",
                "holdout": {"method": "random", "frac": 0.2},
            }
        }
    }
    pinned = {
        "data": {
            "units": {
                "from": "index.csv",
                "key": "patient_id",
                "holdout": {"method": "random", "frac": 0.2, "seed": 1234},
            }
        }
    }
    other_pin = {
        "data": {
            "units": {
                "from": "index.csv",
                "key": "patient_id",
                "holdout": {"method": "random", "frac": 0.2, "seed": 9999},
            }
        }
    }
    assert design_digest(base) == design_digest(pinned)
    assert design_digest(pinned) == design_digest(other_pin)

    widened = {
        "data": {
            "units": {
                "from": "index.csv",
                "key": "patient_id",
                "holdout": {"method": "random", "frac": 0.3},
            }
        }
    }
    assert design_digest(base) != design_digest(widened)


def test_the_seed_exclusion_covers_assign_and_holdout_together():
    """One config carrying both pins. Asserted together because the two
    exclusions are one function: an implementation that returned early after
    rewriting `assign` would leave `holdout.seed` in, and a config with only
    one pin cannot tell that apart from a correct one."""

    def cfg(assign_seed, holdout_seed):
        return {
            "data": {
                "units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "assign": {"arm": {"method": "random", "seed": assign_seed}},
                    "holdout": {"method": "random", "frac": 0.2, "seed": holdout_seed},
                }
            }
        }

    assert design_digest(cfg(7, 11)) == design_digest(cfg(8, 12))
    # A non-seed edit inside the assign block still moves it, so the
    # exclusion is per-field rather than per-block. (The holdout half of that
    # claim is pinned separately, in test_a_pinned_holdout_seed_does_not_move_
    # the_design_digest's "widened" case.)
    moved = {
        "data": {
            "units": {
                "from": "index.csv",
                "key": "patient_id",
                "assign": {"arm": {"method": "blocked", "seed": 7}},
                "holdout": {"method": "random", "frac": 0.2, "seed": 11},
            }
        }
    }
    assert design_digest(cfg(7, 11)) != design_digest(moved)


def test_a_non_mapping_assign_does_not_block_the_holdout_seed_exclusion():
    """The old implementation returned early whenever `assign` was not a
    mapping, so a config with a non-mapping `assign` AND a pinned
    `holdout.seed` would have kept the holdout seed in the digest. The
    holdout exclusion must be reached regardless of what `assign` holds."""
    pinned = {
        "data": {
            "units": {
                "assign": "nonsense",
                "holdout": {"method": "random", "frac": 0.2, "seed": 1},
            }
        }
    }
    unseeded = {
        "data": {
            "units": {
                "assign": "nonsense",
                "holdout": {"method": "random", "frac": 0.2},
            }
        }
    }
    assert design_digest(pinned) == design_digest(unseeded)


def test_the_seed_exclusion_never_raises_on_a_shape_it_did_not_expect():
    """`validate` reaches `design_digest` before a config is known-good, so a
    non-mapping `holdout` must be left exactly as given rather than unpacked.
    Each of these must return a digest instead of raising."""
    for holdout in ("nonsense", ["a", "list"], 3, None):
        assert design_digest({"data": {"units": {"holdout": holdout}}}).startswith("sha256:")


# --- H8b task 13, arm G: parameters_hash agrees with its own embedded ------
# config. Captured at `0a636af` by running. NEVER MOVES IN THIS SLICE — task 7
# rewrites `parameters_hash`'s body (extracting `covered_config`) without
# changing what it hashes, and this arm is the pin that would catch it if it
# did.


def test_h8b_arm_g_parameters_hash_agrees_with_run_yamls_embedded_config(tmp_path: Path):
    """The first sub-arm needs a real run, so it drives one —
    `test_h8b_arm_g_metadata_only_change_is_identical` and
    `test_h8b_arm_g_max_failed_fraction_change_differs` are pure-function
    checks and need none. No existing test in this file compares
    `parameters_hash` against a real `run.yaml`'s own recorded value; every
    existing test here calls the function directly on a hand-built dict.
    This is new coverage."""
    import yaml
    from tests.test_cli import run_a_project

    doc = run_a_project(
        tmp_path,
        replication={"repeats": [{"kind": "seed", "n": 2}]},
        units=8,
        sweep={"grid": {"analysis.method": ["pearson", "spearman"]}},
    )
    run_doc = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert parameters_hash(run_doc["config"]) == run_doc["parameters_hash"]


def test_h8b_arm_g_metadata_only_change_is_identical():
    """Fixture M's first arm, at the function level. `metadata.description`
    moves, nothing else. This is the SAME claim
    `test_parameters_hash_excludes_metadata_and_the_two_paths` already makes
    (over a different literal — `metadata.name`/`description` together
    there, `description` alone here) — restated for arm G's own record, not
    new coverage."""
    base = {
        "experiment_type": "generic",
        "metadata": {"name": "a", "description": "one"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
        "limits": {"max_failed_fraction": 0.1},
    }
    changed = {**base, "metadata": {**base["metadata"], "description": "a different description"}}
    assert parameters_hash(base) == parameters_hash(changed)


def test_h8b_arm_g_max_failed_fraction_change_differs():
    """Fixture M's second arm, at the function level: `limits` is inside the
    hash, so a `limits.max_failed_fraction` edit and nothing else must
    differ. No existing test in this file edits `limits` specifically — the
    nearest neighbour edits `data.input_manifest_policy` — so this is new
    coverage for this key, even though it is the same *shape* of assertion
    as the existing `parameters.analysis.method` edit."""
    base = {
        "experiment_type": "generic",
        "metadata": {"name": "a", "description": "one"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
        "limits": {"max_failed_fraction": 0.1},
    }
    changed = {**base, "limits": {"max_failed_fraction": 0.9}}
    assert parameters_hash(base) != parameters_hash(changed)


def test_h8b_covered_config_is_the_exact_projection_parameters_hash_hashes():
    """H8b task 7, Decision 3: `covered_config` is the extraction of
    `parameters_hash`'s own inline projection — every top-level key except
    `metadata`, with `data` narrowed to everything but `input_dir` and
    `output_dir`. This is the pin that `parameters_hash` now calls
    `covered_config` rather than reimplementing it: hashing `covered_config`'s
    own return must equal `parameters_hash`'s output, for a config carrying
    every excluded field at once so the projection is exercised on all three
    exclusions in one fixture."""
    import hashlib
    import json

    config = {
        "experiment_type": "generic",
        "metadata": {"name": "a", "description": "one", "authors": ["x"]},
        "data": {
            "input_dir": "/x",
            "output_dir": "/y",
            "input_manifest_policy": "hash_all",
            "units": {"key": "patient_id"},
        },
        "parameters": {"analysis": {"method": "pearson"}},
        "limits": {"max_failed_fraction": 0.1},
    }
    covered = covered_config(config)
    assert "metadata" not in covered
    assert "input_dir" not in covered["data"]
    assert "output_dir" not in covered["data"]
    assert covered["data"]["input_manifest_policy"] == "hash_all"
    assert covered["data"]["units"] == {"key": "patient_id"}
    assert covered["parameters"] == {"analysis": {"method": "pearson"}}
    assert covered["limits"] == {"max_failed_fraction": 0.1}
    canonical = json.dumps(covered, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    expected = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
    assert parameters_hash(config) == expected


def test_h8b_covered_config_does_not_mutate_input():
    """The same non-mutation property `test_parameters_hash_does_not_mutate_input`
    pins for `parameters_hash`, restated directly against the extracted
    function — `covered_config` builds new dicts rather than editing the
    caller's."""
    config = {
        "metadata": {"name": "a"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
    }
    before = {
        "metadata": {"name": "a"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
    }
    covered_config(config)
    assert config == before


# ---------------------------------------------------------------------------
# H6a's guard pin — arms D and E, captured in batch 1 BEFORE any code task
# runs. Arms A, B and C are in `tests/test_cli.py`, arm F in
# `tests/test_validate.py`, and arm N in `tests/test_diff.py`.
#
# These two arms bring the first `git init` into this module: `grep -c
# "git init\|subprocess" tests/test_hashes.py` was 0 before them. Arm D needs
# real repositories because the property it holds — tracked or not — is not
# observable through `code_hash` today and becomes observable at task 5.

# Fixture D's and Fixture E's shared digest, computed here by building both
# trees and calling the shipped `code_hash`. The plan's `6ddb8634…` is NOT
# reproducible from the design's own stated tree (§ Corrections 5: the `.pyd`'s
# bytes are never stated and nine candidates were tried), so no task asserts
# it; the bytes are fixed at `X` and this is what they produce.
_H6A_TRACKED_PYD_DIGEST = "sha256:eec1541edde45c11c395e788000f719a48965a8f6fd2b3772a56de92cca18dc2"

# The zero-file digest: `sha256` of the empty string.
_H6A_EMPTY_DIGEST = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def _h6a_commit(root: Path, *paths: str) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", "."], cwd=root, check=True)
    subprocess.run(["git", "add", "-f", *paths], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "pin"],
        cwd=root,
        check=True,
    )


def test_h6a_arm_d_a_tracked_excluded_file_is_hashed_and_a_pycache_one_is_not(tmp_path: Path):
    """Arm D. NO AUTHORIZED EDITOR — a passing arm IS the proof.

    Two trees, one digest. Fixture D commits `src/pkg/loose.pyd` with
    `git add -f`, so it is **tracked** while matching the scaffold's own
    `*.py[cod]` pattern: git does not skip a tracked file, so neither does the
    hash — the second of § How the three are computed's four cases. Fixture E
    adds a **tracked** `src/pkg/__pycache__/keep.py` on top, which the fixed
    skip set drops before git is asked anything — the first case, and the
    positive control for § Templates' *"unconditionally"*.

    **Why the arm is built on the AFTER value.** The design's own table has the
    untracked-`.pyd` tree carrying the *same* digest in the *today* column,
    because today's `code_hash` cannot tell tracked from untracked at all. An
    assertion on the today column would therefore pass under a mutation that
    drops tracked files too. `eec1541e…` is the after value; that it is also
    the today value is what lets this arm be captured green now, and it is the
    coincidence a fixture must not be built on.

    There is no editor who could make this arm pass another way: after task 5
    the same two trees must still produce the same one digest.

    **Task 3's one mechanical touch here is the same as arm E's.** `include`
    becoming required means this test's two `code_hash(...)` calls need the
    literal `None` to keep importing at all — no `assert` line moves, and the
    digest literal below is untouched.
    """
    d_tree = tmp_path / "fixture_d"
    write(d_tree, ".gitignore", ".env\n__pycache__/\n*.py[cod]\n.venv/\n")
    write(d_tree, "src/pkg/step.py", "a = 1\n")
    write(d_tree, "templates/t.py", "b = 2\n")
    write(d_tree, "src/pkg/loose.pyd", "X")
    _h6a_commit(d_tree, ".gitignore", "src/pkg/step.py", "templates/t.py", "src/pkg/loose.pyd")
    assert code_hash(d_tree, None) == _H6A_TRACKED_PYD_DIGEST

    e_tree = tmp_path / "fixture_e"
    write(e_tree, ".gitignore", ".env\n__pycache__/\n*.py[cod]\n.venv/\n")
    write(e_tree, "src/pkg/step.py", "a = 1\n")
    write(e_tree, "templates/t.py", "b = 2\n")
    write(e_tree, "src/pkg/loose.pyd", "X")
    write(e_tree, "src/pkg/__pycache__/keep.py", "k = 1\n")
    _h6a_commit(
        e_tree,
        ".gitignore",
        "src/pkg/step.py",
        "templates/t.py",
        "src/pkg/loose.pyd",
        "src/pkg/__pycache__/keep.py",
    )
    # Both files really are tracked — otherwise this arm would be two
    # statements about untracked files, which today's hash treats identically
    # and which would make the whole arm blind after task 5.
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files"], cwd=e_tree, capture_output=True, text=True, check=True
    ).stdout.split()
    assert "src/pkg/loose.pyd" in tracked
    assert "src/pkg/__pycache__/keep.py" in tracked
    assert code_hash(e_tree, None) == _H6A_TRACKED_PYD_DIGEST


def test_h6a_arm_e_code_hash_of_a_directory_that_does_not_exist_is_the_empty_digest(
    tmp_path: Path,
):
    """Arm E. **TASK 3 IS THE SOLE AUTHORIZED EDITOR.**

    `code_hash` of a directory that does not exist returns the `sha256` of the
    empty string, and it must keep doing so: H6a's zero-file refusal is
    `E-CODE-EMPTY` **at the caller** (`cli.command_run`), never here. Two
    shipped tests in this module rest on that value as a **negative control** —
    `test_code_hash_skip_list_matches_relative_path_not_absolute` and
    `test_code_hash_handles_a_dot_git_intermediate_path_component`, both of
    which compare a real tree's digest against `code_hash(tmp_path /
    "nonexistent_empty_repo")`. Grepped for, not assumed: `grep -n
    "nonexistent_empty_repo" tests/test_hashes.py` names those two and nothing
    else, and neither states the digest as a literal, which is why this arm
    states it as a standalone claim.

    **Task 3's only edit here is adding the literal `None` argument** where the
    call is made, in this test and at the 13 `code_hash(` call sites the
    six named tests in `test_code_hash_covers_src_and_templates_only` through
    `test_code_hash_handles_a_dot_git_intermediate_path_component` already had
    when task 3's brief was written. **No assertion in this arm changes**; a
    task 3 diff that touches an `assert` line here is a finding.

    **A stale count, corrected rather than trusted.** Batch 1 (task 2) added
    this arm and arm D's test AFTER the brief's `grep -c "code_hash("` was
    run, so the 13-plus-`cli.py` count of "no 15th site" no longer covers the
    module: arm D's test and this one add four more calls
    (`test_h6a_arm_d_a_tracked_excluded_file_is_hashed_and_a_pycache_one_is_not`
    and this test), all of which needed the same mechanical `None` for the
    module to import at all — not just typecheck. None of the four is a 15th
    *production* call site.
    """
    assert code_hash(tmp_path / "nonexistent_empty_repo", None) == _H6A_EMPTY_DIGEST
    # Not implied by the line above: an existing directory holding nothing the
    # two trees cover resolves to the same digest, which is the reachable half
    # of the zero-file case and the reason the refusal cannot live here.
    (tmp_path / "empty_repo" / "src").mkdir(parents=True)
    assert code_hash(tmp_path / "empty_repo", None) == _H6A_EMPTY_DIGEST


# ---------------------------------------------------------------------------
# H6a task 5 — Fixtures C, D and D′, over the plan's base tree, through the
# two-step form `cli.command_run` now uses: `hashed_files(root, include)` then
# `code_hash_of`. The base tree is NOT runnable — `templates/t.py` is
# discovered as a project-local template and `validate` refuses with
# `E-TEMPLATE-LOAD`, which is the disagreement batch 1 recorded for arms A and
# B — so the end-to-end half of these claims lives in `tests/test_cli.py`,
# against a runnable project, and this half asserts the digests the plan
# states. Every literal below was computed by building the tree and running,
# never transcribed.

# The base tree's digest, before and after: `code_hash` over `src/pkg/step.py`
# and `templates/t.py`, both tracked. The same value `tests/test_provenance.py`
# and guard-pin arm A hold, each computed independently over its own tree.
_H6A_BASE_DIGEST = "sha256:71bf339cc9463f4c776c711f3d65ccf9b3bc1e18d383b78ae7d4e5170b526c2b"
# Fixture C's tree under the PRE-SLICE definition — every file these trees
# hold, excluded or not.
_H6A_FIXTURE_C_PRE_SLICE_DIGEST = (
    "sha256:1947d2a21da33a9c6e4b3a45448ae11ac89e0399797c53168569a297a3f46bcf"
)


def _h6a_base_repo(root: Path) -> Path:
    """The plan's base tree, committed: the scaffold's four ignore patterns,
    `src/pkg/step.py` = `a = 1\\n`, `templates/t.py` = `b = 2\\n`."""
    write(root, ".gitignore", ".env\n__pycache__/\n*.py[cod]\n.venv/\n")
    write(root, "src/pkg/step.py", "a = 1\n")
    write(root, "templates/t.py", "b = 2\n")
    _h6a_commit(root, ".gitignore", "src/pkg/step.py", "templates/t.py")
    return root


def _h6a_commit_more(root: Path, *paths: str) -> None:
    """`git add -f` plus a commit in an already-initialized repo — the second
    half of `_h6a_commit`, which does the `git init` a second call cannot."""
    import subprocess

    subprocess.run(["git", "add", "-f", *paths], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "more"],
        cwd=root,
        check=True,
    )


def _h6a_include(root: Path):
    """`command_run`'s own predicate, built the way `command_run` builds it."""
    from publishable.provenance import unignored_under_hashed_trees

    def include(candidates: list[str]) -> set[str]:
        return unignored_under_hashed_trees(root, candidates)

    return include


def test_h6a_fixture_c_the_other_two_unhonoured_patterns_drop_out(tmp_path: Path):
    """Fixture C. Three untracked files matching three different patterns of
    the scaffold's own `.gitignore` — `src/pkg/.env`, `src/.venv/lib/site.py`
    and `src/pkg/loose.pyd` — all moved `code_hash` before this slice and none
    moves it now.

    **Both branches are asserted, and that is what makes this a mutation
    catcher rather than a restatement.** `include=None` is the pre-slice
    definition and still computes `1947d2a2…`, unchanged by this slice;
    the two-step form `command_run` uses computes `71bf339c…`, the base
    tree's own. A mutation that computes the filter and ignores it collapses
    the second onto the first, and the two literals are what tell them apart.

    The helper's own answer is asserted as the exact set of three, so a
    predicate that dropped a fourth file — or the wrong three — could not pass
    by arriving at the right digest through a different subtraction.
    """
    repo = _h6a_base_repo(tmp_path / "repo")
    write(repo, "src/pkg/.env", "OPENAI_API_KEY=sk-live-1\n")
    write(repo, "src/.venv/lib/site.py", "s = 3\n")
    (repo / "src" / "pkg" / "loose.pyd").write_text("X")

    assert code_hash(repo, None) == _H6A_FIXTURE_C_PRE_SLICE_DIGEST

    candidates = [rel for rel, _ in hashed_files(repo, None)]
    kept = _h6a_include(repo)(candidates)
    assert set(candidates) - kept == {
        "src/pkg/.env",
        "src/.venv/lib/site.py",
        "src/pkg/loose.pyd",
    }
    assert code_hash_of(hashed_files(repo, _h6a_include(repo))) == _H6A_BASE_DIGEST


def test_h6a_fixture_d_a_tracked_file_matching_a_pattern_is_still_hashed(tmp_path: Path):
    """Fixtures D and D′ — the same `src/pkg/loose.pyd` = `X`, tracked in one
    tree and untracked in the other, through the wired two-step form.

    **The bytes are `X` and the literal is `eec1541e…`** (§ Corrections 5): the
    design's `6ddb8634…` is not reproducible from its own stated tree, because
    the `.pyd`'s bytes were never stated, and nine candidates were tried
    against it. This asserts the recomputed value.

    D′ is the coincidence D must not rest on: untracked, the same tree hashed
    to `eec1541e…` before this slice too, so an assertion on the *today*
    column would pass under a mutation that dropped tracked files as well.
    Here the two trees differ — `eec1541e…` against the base tree's
    `71bf339c…` — which is the whole claim, and `git ls-files` is asserted so
    the tracked arm cannot silently become a second untracked one.
    """
    tracked_pyd = "sha256:eec1541edde45c11c395e788000f719a48965a8f6fd2b3772a56de92cca18dc2"

    d_tree = _h6a_base_repo(tmp_path / "fixture_d")
    (d_tree / "src" / "pkg" / "loose.pyd").write_text("X")
    _h6a_commit_more(d_tree, "src/pkg/loose.pyd")
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files"], cwd=d_tree, capture_output=True, text=True, check=True
    ).stdout.split()
    assert "src/pkg/loose.pyd" in tracked
    assert code_hash_of(hashed_files(d_tree, _h6a_include(d_tree))) == tracked_pyd

    d_prime = _h6a_base_repo(tmp_path / "fixture_d_prime")
    (d_prime / "src" / "pkg" / "loose.pyd").write_text("X")
    untracked = subprocess.run(
        ["git", "ls-files"], cwd=d_prime, capture_output=True, text=True, check=True
    ).stdout.split()
    assert "src/pkg/loose.pyd" not in untracked
    # The coincidence, stated: the two trees are byte-identical, and the
    # pre-slice definition cannot tell them apart at all.
    assert code_hash(d_prime, None) == tracked_pyd
    assert code_hash_of(hashed_files(d_prime, _h6a_include(d_prime))) == _H6A_BASE_DIGEST


# ---------------------------------------------------------------------------
# H6a task 6 — Fixture J: the hash and the dirty gate agree.


def test_h6a_fixture_j_the_gate_and_the_hash_agree_on_an_excluded_file(tmp_path: Path):
    """Fixture J, one tree and two assertions, so neither half can move alone.

    **They do not share a file list, and a docstring claiming they did would be
    a false claim.** They share `HASHED_TREES` — one constant, one pathspec —
    and ask git two different questions: `git status --porcelain -- src
    templates` (has anything moved?) and `git check-ignore` (is this path
    excluded?). `status` never lists a clean tracked file, so it cannot
    produce the hash's file list. What is pinned here is behavioural
    agreement.

    The four states of a file under the two trees, and what each is now:

      * untracked and not excluded — **dirty**, and **hashed**
      * tracked and modified — **dirty**, and **hashed**
      * tracked and clean — not dirty, and **hashed**
      * present but excluded — **neither**

    Before this slice the last one was *not dirty and hashed*: the gate
    consulted git and the hash did not, so one mechanism said *nothing
    changed* while the other said *the code moved*. That disagreement is what
    this slice closed, and this is the tree it closed it on — Fixture B's,
    the credentials case.
    """
    from publishable.provenance import git_provenance

    repo = _h6a_base_repo(tmp_path / "repo")
    write(repo, "src/pkg/.env", "OPENAI_API_KEY=sk-live-1\n")
    # `config_path` is the gate's second argument and answers a different
    # question (`config_committed`); any tracked path in the repo serves, and
    # this one is committed by `_h6a_base_repo`.
    committed = repo / "src" / "pkg" / "step.py"

    assert git_provenance(repo, committed).code_dirty is False
    assert "src/pkg/.env" not in {rel for rel, _ in hashed_files(repo, _h6a_include(repo))}
    # The control: the gate CAN see this tree, and the hash CAN see a path
    # under it. Without it both halves would pass over a repository where
    # nothing was measured at all.
    write(repo, "src/pkg/loose.py", "c = 3\n")
    assert git_provenance(repo, committed).code_dirty is True
    assert "src/pkg/loose.py" in {rel for rel, _ in hashed_files(repo, _h6a_include(repo))}
