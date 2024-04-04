from typing import List

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet


def validate_filter(
        model: models,
        required_values: dict = None,
        or_conditions: List[List] = None
) -> bool:

    model_fields = [field.name for field in model._meta.get_fields()]
    for field in required_values:
        if field not in model_fields:
            return False

    for alternative in or_conditions:
        for field in alternative:
            if field not in model_fields:
                return False

    return True


def create_qfilter(
        required_values: dict = None,
        or_conditions: List[List] = None
) -> Q:

    values_dict = {}
    qfilter_elems = []
    qfilter = Q()

    for field in required_values:
        if not isinstance(required_values[field], List):
            required_values[field] = [required_values[field]]
        temp = Q()
        for val in required_values[field]:
            temp |= Q(**{field: val})
        values_dict[field] = temp

    for alternative in or_conditions:
        temp = Q()
        for field in alternative:
            temp |= values_dict[field]
            values_dict.pop(field)
        qfilter_elems.append(temp)

    for field in values_dict:
        qfilter_elems.append(values_dict[field])

    for elem in qfilter_elems:
        qfilter &= elem

    return qfilter


def get_queryset(
        model: models,
        required_values: dict = None,
        or_required: List[List] or List = None,
        forbidden_values: dict = None,
        or_forbidden: List[List] or List = None
) -> QuerySet:

    if not or_required:
        or_required = [[]]
    if not isinstance(or_required[0], List):
        or_required = [or_required]
    if not required_values:
        required_values = {}
    if not or_forbidden:
        or_forbidden = [[]]
    if not isinstance(or_forbidden[0], List):
        or_forbidden = [or_forbidden]
    if not forbidden_values:
        forbidden_values = {}

    if not validate_filter(model, required_values, or_required):
        raise ValidationError('Discrepancy between model fields and filter elements.')
    if not validate_filter(model, forbidden_values, or_forbidden):
        raise ValidationError('Discrepancy between model fields and filter elements.')

    queryset = model.objects.filter(create_qfilter(required_values, or_required))
    return queryset.exclude(create_qfilter(forbidden_values, or_forbidden))
