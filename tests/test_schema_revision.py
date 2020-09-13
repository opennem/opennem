import pytest
from pydantic import ValidationError

from opennem.schema.opennem import RevisionSchema


class TestSchemaRevision(object):
    def test_empty_errors(self):
        with pytest.raises(ValidationError) as exc:
            RevisionSchema()

            assert isinstance(
                exc, ValidationError
            ), "No fields raises validationerror"
