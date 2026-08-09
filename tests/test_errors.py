import pytest

from publishable import ArtifactError, ArtifactExistsError, ContractError, PublishableError


def test_hierarchy_is_two_levels_with_one_leaf():
    assert issubclass(ContractError, PublishableError)
    assert issubclass(ArtifactError, PublishableError)
    assert issubclass(ArtifactExistsError, ArtifactError)
    assert not issubclass(ContractError, ArtifactError)


def test_every_error_carries_its_code():
    err = ContractError("bad path", code="E-STEP-PARAM-UNKNOWN")
    assert err.code == "E-STEP-PARAM-UNKNOWN"
    assert "bad path" in str(err)


def test_catching_the_base_catches_everything():
    with pytest.raises(PublishableError):
        raise ArtifactExistsError("already there", code="E-ARTIFACT-EXISTS")
