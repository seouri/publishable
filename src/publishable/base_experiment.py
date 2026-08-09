"""The ordered steps list, and nothing else."""

from publishable.base_step import BaseStep


class BaseExperiment:
    steps: list[type[BaseStep]] = []
