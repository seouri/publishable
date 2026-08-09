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
