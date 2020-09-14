from typing import Any, List, Union

from dictalchemy.utils import asdict
from pydantic import BaseModel

from opennem.db.models.opennem import BaseModel as BaseDbModel


def compare_record_differs(
    subject: object, target: object, fields: Union[str, List[str]]
) -> bool:
    """
        Compare two objects or types returns True if they're the same

    """

    if not type(fields) is list:
        fields = [fields]

    comparator_results = []

    for field in fields:
        subject_value = field_getter(subject, field)
        target_value = field_getter(target, field)

        if target_value in [None, {}, ""]:
            return False

        result = subject_value != target_value

        comparator_results.append(result)

    return all(comparator_results)


def compare_field(subject: Any, target: Any) -> bool:
    pass


def field_getter(subject: object, field_name: str, default: any = None):
    """
        Gets a field value from a dict or object

    """
    value = None

    if type(subject) is dict and field_name in subject:
        value = subject.get(field_name, default)

    if hasattr(subject, field_name):
        value = getattr(subject, field_name, default)

    if isinstance(value, BaseModel):
        value: dict = value.dict()

    if isinstance(value, BaseDbModel):
        value: dict = asdict(
            value, exclude=["created_by", "created_at", "updated_at"]
        )

    if value:
        return value

    return default
