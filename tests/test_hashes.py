from pathlib import Path

from publishable.hashes import code_hash, design_digest, parameters_hash, short


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_code_hash_covers_src_and_templates_only(tmp_path: Path):
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    write(tmp_path, "templates/mine.py", "b = 2\n")
    before = code_hash(tmp_path)
    write(tmp_path, "docs/notes.md", "unrelated\n")
    write(tmp_path, "configs/c/config.yaml", "x: 1\n")
    assert code_hash(tmp_path) == before, "changes outside the two trees must not move it"
    write(tmp_path, "src/pkg/step.py", "a = 2\n")
    assert code_hash(tmp_path) != before


def test_code_hash_ignores_pycache(tmp_path: Path):
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    before = code_hash(tmp_path)
    write(tmp_path, "src/pkg/__pycache__/step.cpython-311.pyc", "junk")
    assert code_hash(tmp_path) == before


def test_code_hash_is_prefixed_and_short_takes_seven(tmp_path: Path):
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    h = code_hash(tmp_path)
    assert h.startswith("sha256:")
    assert len(short(h)) == 7


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
    empty_digest = code_hash(tmp_path / "nonexistent_empty_repo")
    h = code_hash(repo)
    assert h != empty_digest
    write(repo, "src/pkg/step.py", "a = 2\n")
    assert code_hash(repo) != h


def test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree(tmp_path: Path):
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    before = code_hash(tmp_path)
    write(tmp_path, "src/pkg/__pycache__/step.cpython-311.pyc", "junk")
    assert code_hash(tmp_path) == before


def test_code_hash_handles_a_dot_git_intermediate_path_component(tmp_path: Path):
    repo = tmp_path / ".git" / "repo"
    write(repo, "src/pkg/step.py", "a = 1\n")
    empty_digest = code_hash(tmp_path / "nonexistent_empty_repo")
    assert code_hash(repo) != empty_digest


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
    """The first sub-arm needs a real run, so it drives one — the two below
    are pure-function checks and need none. No existing test in this file
    compares `parameters_hash` against a real `run.yaml`'s own recorded
    value; every existing test here calls the function directly on a
    hand-built dict. This is new coverage."""
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
