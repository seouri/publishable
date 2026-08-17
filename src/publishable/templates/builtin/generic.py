from publishable.materialize import TEMPLATE_VERSION
from publishable.param import Param
from publishable.templates.base import BaseTemplate


class GenericTemplate(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    field_convention = "generic"
    default_repeats = 1
    required_env: list[str] = []
    apparatus_probe = None
    apparatus_facts: list[str] = []
    version = TEMPLATE_VERSION

    parameter_spec = {
        "analysis.method": Param(
            str, default="pearson", choices=["pearson", "spearman", "kendall"]
        ),
        "analysis.min_samples": Param(int, default=30, ge=2),
        "analysis.confidence": Param(float, default=0.95, gt=0, lt=1),
        "analysis.drop_missing": Param(
            bool, default=True, help="Drop rows with any missing value before analysis"
        ),
    }
