from importlib import import_module
from typing import Dict, List, Type, TypeVar, Union

from django.contrib.auth.models import ContentType, Group, Permission
from django.db import models
from django.db.models.query import QuerySet

from core.choices import BasicModelAction

model_cls = TypeVar('model_cls', bound=Type[models.Model])


def get_all_permissions_for_model(model: model_cls) -> Union[QuerySet, List[Permission]]:
    """
    Returns all permissions for given model.

    :param model: Model to get permissions for.
    :type model: Type[models.Model]

    :return: List of permissions for given model.
    :rtype: QuerySet[Permission]
    """
    return Permission.objects.filter(
        content_type=ContentType.objects.get_for_model(model).id
    )


def get_all_models_from_app(app_label: str) -> Dict[str, model_cls]:
    """
    Returns all models from given app. App has to have the `__all__` variable defined in models.py.

    :param app_label: Name of the app.
    :type app_label: str

    :return: Dictionary of models from given app. Keys are model names, values are model classes.
    :rtype: Dict[str, Type[models.Model]]
    """
    module = import_module(f'{app_label}.models')
    return {model: getattr(module, model) for model in module.__all__}


def get_model_permission_by_label(model: model_cls, perm_label: str) -> Permission:
    """
    Returns permission object for a given model and permission label.

    :param model: Model to get permission for.
    :type model: Type[models.Model]
    :param perm_label: Permission label (e.g. 'add', 'change', 'view', 'delete').
    :type perm_label: str

    :return: Permission object with codename equal to '`label`' + '_' + '`model name`'.
    :rtype: Permission
    """
    return Permission.objects.get(codename=f'{perm_label}_{model._meta.model_name}')


def get_model_permissions(
        model: model_cls,
        permissions: BasicModelAction | List[BasicModelAction] = 'all'
) -> QuerySet[Permission]:
    """
    Returns QuerySet of basic permissions objects for given model. If permissions is set to 'all'
    (default), all basic permissions for given model are returned, otherwise only specified
    permissions are returned.

    Basic permissions are the permissions automatically created by Django for each model (add,
    change, view, delete).

    :param model: Model to get permissions for.
    :type model: Type[models.Model]
    :param permissions: List of permissions to get. If set to 'all' (default), all basic permissions
        are returned. Can be set to a list of BasicPermissionAction or a single BasicModelAction.
    :type permissions: BasicModelAction | List[BasicPermissionType]

    :return: QuerySet of basic permissions for given model.
    :rtype: QuerySet[Permission]
    """
    if permissions == 'all':
        permissions = [p for p in BasicModelAction]
    elif isinstance(permissions, BasicModelAction):
        permissions = [f'{permissions.label}_{model._meta.model_name}']
    elif isinstance(permissions, List):
        permissions = [f'{p.label}_{model._meta.model_name}' for p in permissions]

    return Permission.objects.filter(codename__in=permissions)


def delete_populated_group(group: Group) -> None:
    """
    Deletes a group along with all its user and permission assignments (does not delete the users or
    permissions themselves).

    :param group: Group to delete.
    :type group: Group
    """

    group.user_set.clear()
    group.permissions.clear()
    group.delete(using='default')


def delete_populated_groups(groups: List[Group]) -> None:
    """
    Deletes a list of groups along with all their user and permission assignments (does not
    delete the users or permissions themselves).

    :param groups: List of groups to delete.
    :type groups: List[Group]
    """

    for group in groups:
        delete_populated_group(group)
