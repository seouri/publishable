"""A second module defining a class with the same name as one in test_scope.py,
used only to exercise the step-name collision check in `build_plan`.
"""

from publishable import BaseStep


class Analyze(BaseStep):
    scope = "repeat"

    def run(self, cfg, io): ...
