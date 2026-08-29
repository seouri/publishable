from publishable.diagnostics import EXIT_OK, EXIT_WRONG, Collector


def test_collector_accumulates_rather_than_stopping():
    c = Collector()
    c.error("E-PARAM-UNKNOWN", "parameters.analysis.min_sample", "did you mean min_samples?")
    c.error("E-META-REQUIRED", "metadata.description", "is empty")
    c.warn("W-STATS-FAMILY", "statistics.correction", "family of 15 with correction: none")
    assert len(c.findings) == 3
    assert c.has_errors


def test_a_warning_alone_is_not_an_error():
    c = Collector()
    c.warn("W-REPL-FLOOR", "replication.repeats", "below the class default")
    assert not c.has_errors
    assert c.exit_code() == EXIT_OK


def test_errors_set_exit_one():
    c = Collector()
    c.error("E-DATA-IN-REPO", "data.output_dir", "resolves inside the git repository")
    assert c.exit_code() == EXIT_WRONG


def test_render_puts_the_identifier_beside_the_finding():
    c = Collector()
    c.error("E-PARAM-UNKNOWN", "parameters.analysis.min_sample", "did you mean `min_samples`?")
    out = c.render()
    assert "E-PARAM-UNKNOWN" in out
    assert "parameters.analysis.min_sample" in out
    assert "1 problem (1 error, 0 warnings)" in out


def test_render_pluralizes_error_and_warning_independently():
    c = Collector()
    c.error("E-PARAM-UNKNOWN", "parameters.analysis.min_sample", "did you mean `min_samples`?")
    c.warn("W-STATS-FAMILY", "statistics.correction", "family of 15 with correction: none")
    out = c.render()
    assert "2 problems (1 error, 1 warning)" in out


def test_render_pluralizes_multiple_errors():
    c = Collector()
    c.error("E-PARAM-UNKNOWN", "parameters.analysis.min_sample", "did you mean `min_samples`?")
    c.error("E-META-REQUIRED", "metadata.description", "is empty")
    out = c.render()
    assert "2 problems (2 errors, 0 warnings)" in out


def test_render_handles_empty_findings():
    c = Collector()
    out = c.render()
    assert "0 problems (0 errors, 0 warnings)" in out


def test_disclosed_has_the_four_keys():
    c = Collector()
    c.error("E-PARAM-UNKNOWN", "parameters.analysis.min_sample", "did you mean `min_samples`?")
    [finding] = c.disclosed()
    assert set(finding.keys()) == {"level", "code", "path", "message"}
    assert finding["level"] == "error"
    assert finding["code"] == "E-PARAM-UNKNOWN"
    assert finding["path"] == "parameters.analysis.min_sample"
    assert finding["message"] == "did you mean `min_samples`?"


def test_disclosed_redacts_the_same_credential_render_does():
    c = Collector()
    c.credentials = {"OPENAI_API_KEY": "sk-super-secret-value"}
    c.error("E-RESOLVER-RAISED", "data.units", "auth failed for sk-super-secret-value")
    [finding] = c.disclosed()
    assert "sk-super-secret-value" not in finding["message"]
    assert "<redacted:OPENAI_API_KEY>" in finding["message"]
    # The same redaction `render` applies on the same field, so the two surfaces agree.
    assert finding["message"] in c.render()


def test_disclosed_leaves_the_message_unchanged_with_no_credentials():
    c = Collector()
    c.warn("W-ENV-UNLOCKED", "environment", "no uv.lock found; the environment is not pinned")
    [finding] = c.disclosed()
    assert finding["message"] == "no uv.lock found; the environment is not pinned"
