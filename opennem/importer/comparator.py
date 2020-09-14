from typing import Any, List


def compare_record(subject: object, target: object, fields: List[str]) -> bool:

    comparator_results = []

    for field in fields:
        subject_value = field_getter(subject, field)
        target_value = field_getter(subject, field)

        result = subject_value == target_value

        comparator_results.append(result)

    return all(comparator_results)


def compare_field(subject: Any, target: Any) -> bool:
    pass


def field_getter(subject: object, field_name: str):
    if hasattr(subject, field_name):
        return getattr(subject, field_name, None)
