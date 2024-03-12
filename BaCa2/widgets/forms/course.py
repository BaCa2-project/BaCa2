import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from core.choices import ResultStatus, TaskJudgingMode
from core.tools.files import CsvFileHandler, FileHandler
from course.models import Round, Submit, Task
from course.routing import InCourse
from main.models import Course, Role, User
from util.models_registry import ModelsRegistry
from widgets.forms.base import (
    BaCa2ModelForm,
    FormElementGroup,
    FormObserver,
    FormObserverTab,
    FormWidget
)
from widgets.forms.fields import (
    AlphanumericStringField,
    ChoiceField,
    DateTimeField,
    FileUploadField,
    ModelChoiceField
)
from widgets.forms.fields.course import CourseName, CourseShortName, USOSCode
from widgets.forms.fields.table_select import TableSelectField
from widgets.listing.columns import TextColumn
from widgets.navigation import SideNav
from widgets.popups.forms import SubmitConfirmationPopup

logger = logging.getLogger(__name__)


# ---------------------------------- course form base classes ---------------------------------- #

class CourseModelForm(BaCa2ModelForm):
    """
    Base class for all forms in the BaCa2 app which are used to create, delete or modify course
    database model objects.

    See also:
        - :class:`BaCa2ModelForm`
        - :class:`CourseActionForm`
    """

    @classmethod
    @abstractmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is permissible and the form data is valid.

        :param request: Request object.
        :type request: HttpRequest
        :return: Dictionary containing a success message and any additional data to be included in
            the response.
        :rtype: Dict[str, Any]
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @classmethod
    def is_permissible(cls, request) -> bool:
        """
        Checks if the user making the request has the permission to perform the action specified by
        the form within the scope of the current course.
        """
        return request.user.has_course_permission(cls.ACTION.label, InCourse.get_context_course())


class CourseActionForm(BaCa2ModelForm, ABC):
    """
    Base class for all forms in the BaCa2 app which are used to perform course-specific actions
    on default database model objects (such as adding or removing members, creating roles, etc.).
    All form widgets wrapping this form should post to the course model view url with a specified
    `course_id` parameter. The form's `is_permissible` checks if the requesting user has the
    permission to perform its action within the scope of the course with the given ID.

    See also:
        - :class:`BaCa2ModelForm`
        - :class:`Course.CourseAction`
    """

    #: Actions performed by this type of form always concern the :class:`Course` model.
    MODEL = Course
    #: Course action to be performed by the form.
    ACTION: Course.CourseAction = None

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is permissible and the form data is valid.

        :param request: Request object.
        :type request: HttpRequest
        :return: Dictionary containing a success message and any additional data to be included in
            the response.
        :rtype: Dict[str, Any]
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @staticmethod
    def get_context_course(request) -> Course:
        """
        :return: Course object matching the course ID provided in the request.
        :rtype: Course
        :raises ValueError: If the request object does not have a course attribute or the course ID
            is not provided in the request.
        """
        if not hasattr(request, 'course'):
            raise ValueError('Request object does not have a course attribute')

        course_id = request.course.get('course_id')

        if not course_id:
            raise ValueError('Course ID not provided in the request')

        return ModelsRegistry.get_course(int(course_id))

    @classmethod
    def is_permissible(cls, request) -> bool:
        """
        :param request: Request object.
        :type request: HttpRequest
        :return: `True` if the user has the permission to perform the action specified by the form
            within the scope of the course with the ID provided in the request, `False` otherwise.
        :rtype: bool
        """
        course = cls.get_context_course(request)
        return request.user.has_course_permission(cls.ACTION.label, course)


# =========================================== COURSE =========================================== #

# ---------------------------------------- create course --------------------------------------- #

class CreateCourseForm(BaCa2ModelForm):
    """
    Form for creating new :class:`main.Course` records.
    """

    MODEL = Course
    ACTION = Course.BasicAction.ADD

    #: New course's name.
    course_name = CourseName(label=_('Course name'), required=True)

    #: New course's short name.
    short_name = CourseShortName()

    #: Subject code of the course in the USOS system.
    USOS_course_code = USOSCode(
        label=_('USOS course code'),
        max_length=Course._meta.get_field('USOS_course_code').max_length,
        required=False
    )

    #: Term code of the course in the USOS system.
    USOS_term_code = USOSCode(
        label=_('USOS term code'),
        max_length=Course._meta.get_field('USOS_term_code').max_length,
        required=False
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Creates a new :class:`Course` object based on the data provided in the request.

        :param request: POST request containing the course data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        Course.objects.create_course(
            name=request.POST.get('course_name'),
            short_name=request.POST.get('short_name'),
            usos_course_code=request.POST.get('USOS_course_code'),
            usos_term_code=request.POST.get('USOS_term_code')
        )

        message = _('Course ') + request.POST.get('course_name') + _(' created successfully')
        return {'message': message}


class CreateCourseFormWidget(FormWidget):
    """
    Form widget for the :class:`CreateCourseForm`.
    """

    def __init__(self,
                 request,
                 form: CreateCourseForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param form: Form to be base the widget on. If not provided, a new form will be created.
        :type form: :class:`CreateCourseForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from main.views import CourseModelView

        if not form:
            form = CreateCourseForm()

        super().__init__(
            name='create_course_form_widget',
            request=request,
            form=form,
            post_target_url=CourseModelView.post_url(),
            button_text=_('Add course'),
            toggleable_fields=['short_name'],
            element_groups=FormElementGroup(
                elements=['USOS_course_code', 'USOS_term_code'],
                name='USOS_data',
                toggleable=True,
                toggleable_params={'button_text_off': _('Add USOS data'),
                                   'button_text_on': _('Create without USOS data')},
                frame=True,
                layout=FormElementGroup.FormElementsLayout.HORIZONTAL
            ),
            submit_confirmation_popup=SubmitConfirmationPopup(
                title=_('Confirm course creation'),
                message=_(
                    'Are you sure you want to create a new course with the following data?'
                ),
                confirm_button_text=_('Create course'),
                input_summary=True,
                input_summary_fields=['course_name',
                                      'short_name',
                                      'USOS_course_code',
                                      'USOS_term_code'],
            ),
            **kwargs
        )


# ---------------------------------------- delete course --------------------------------------- #

class DeleteCourseForm(BaCa2ModelForm):
    """
    Form for deleting :class:`main.Course` records.
    """

    MODEL = Course
    ACTION = Course.BasicAction.DEL

    #: ID of the course to be deleted.
    course_id = forms.IntegerField(
        label=_('Course ID'),
        widget=forms.HiddenInput(attrs={'class': 'model-id', 'data-reset-on-refresh': 'true'}),
        required=True,
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Deletes the course with the ID provided in the request.

        :param request: POST request containing the course ID.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        Course.objects.delete_course(int(request.POST.get('course_id')))
        return {'message': _('Course deleted successfully')}


class DeleteCourseFormWidget(FormWidget):
    """
    Form widget for the :class:`DeleteCourseForm`.
    """

    def __init__(self,
                 request,
                 form: DeleteCourseForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param form: Form to be base the widget on. If not provided, a new form will be created.
        :type form: :class:`DeleteCourseForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from main.views import CourseModelView

        if not form:
            form = DeleteCourseForm()

        super().__init__(
            name='delete_course_form_widget',
            request=request,
            form=form,
            post_target_url=CourseModelView.post_url(),
            button_text=_('Delete course'),
            submit_confirmation_popup=SubmitConfirmationPopup(
                title=_('Confirm course deletion'),
                message=_(
                    'Are you sure you want to delete this course? This action cannot be undone.'
                ),
                confirm_button_text=_('Delete course'),
            ),
            **kwargs
        )


# =========================================== MEMBERS ========================================== #

# ----------------------------------------- add members ---------------------------------------- #

class AddMembersForm(CourseActionForm):
    """
    Form for adding members to a course with a specified role.
    """

    ACTION = Course.CourseAction.ADD_MEMBER

    #: Users to be added to the course.
    users = TableSelectField(
        label=_('Choose users to add'),
        table_widget_name='add_members_table_widget',
        data_source_url='',
        cols=[TextColumn(name='email', header=_('Email')),
              TextColumn(name='first_name', header=_('First name')),
              TextColumn(name='last_name', header=_('Last name'))],
    )

    #: Role to be assigned to the newly added members.
    role = ModelChoiceField(
        label=_('Role'),
        data_source_url='',
        label_format_string='[[name]]',
        required=True,
    )

    def __init__(self,
                 *,
                 course_id: int,
                 form_instance_id: int = 0,
                 request=None,
                 **kwargs) -> None:
        """
        :param course_id: ID of the course the form is associated with.
        :type course_id: int
        :param form_instance_id: ID of the form instance. Used to identify the form instance when
            saving its init parameters to the session and to reconstruct the form from the session.
            Defaults to 0. Should be set to a unique value when creating a new form instance within
            a single view with multiple instances of the same form class.
        :type form_instance_id: int
        :param request: HTTP request object received by the view the form is rendered in. Should be
            passed to the constructor if the form is instantiated with custom init parameters.
        :type request: HttpRequest
        :param kwargs: Additional keyword arguments to be passed to the :class:`CourseActionForm`
            super constructor.
        :type kwargs: dict
        """
        from main.views import RoleModelView, UserModelView

        super().__init__(form_instance_id=form_instance_id, request=request, **kwargs)

        self.fields['users'].data_source_url = UserModelView.get_url(
            mode=UserModelView.GetMode.FILTER,
            exclude_params={'roles__course': course_id}
        )

        self.fields['role'].data_source_url = RoleModelView.get_url(
            mode=RoleModelView.GetMode.FILTER,
            filter_params={'course': course_id}
        )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Adds the users selected in the form to the course with the role specified in the form.

        :param request: POST request containing the users and role data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        course = cls.get_context_course(request)
        users = TableSelectField.parse_value(request.POST.get('users'))
        role = int(request.POST.get('role'))

        if role == course.admin_role.id:
            course.add_admins(users)
        else:
            course.add_members(users, role)

        return {'message': _('Members added successfully')}

    @classmethod
    def is_permissible(cls, request) -> bool:
        """
        :param request: Request object.
        :type request: HttpRequest
        :return: `True` if the requesting user has the permission to add members to the course
            specified in the request, `False` otherwise. If the role specified in the request is the
            admin role, the user must have the `ADD_ADMIN` permission.
        :rtype: bool
        """
        course = cls.get_context_course(request)
        role = int(request.POST.get('role'))

        if role == course.admin_role.id:
            return request.user.has_course_permission(Course.CourseAction.ADD_ADMIN.label, course)

        return request.user.has_course_permission(cls.ACTION.label, course)


class AddMembersFormWidget(FormWidget):
    """
    Form widget for the :class:`AddMembersForm`.
    """

    def __init__(self,
                 request,
                 course_id: int,
                 form: AddMembersForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param course_id: ID of the course the view this form widget is rendered in is associated
            with.
        :type course_id: int
        :param form: AddMembersForm to be base the widget on. If not provided, a new form will be
            created.
        :type form: :class:`AddMembers`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from main.views import CourseModelView

        if not form:
            form = AddMembersForm(course_id=course_id, request=request)

        super().__init__(
            name='add_members_form_widget',
            request=request,
            form=form,
            post_target_url=CourseModelView.post_url(**{'course_id': course_id}),
            button_text=_('Add members'),
            **kwargs
        )


class AddMembersFromCSVForm(CourseActionForm):
    """
    Form for adding members from a CSV file to a course.
    """

    ACTION = Course.CourseAction.ADD_MEMBERS_CSV

    #: CSV file containing the members to be added to the course.
    members_csv = FileUploadField(label=_('Members CSV file'),
                                  allowed_extensions=['csv'],
                                  required=True)

    #: Role to be assigned to the newly added members.
    role = ModelChoiceField(
        label=_('Role'),
        data_source_url='',
        label_format_string='[[name]]',
        required=True,
    )

    def __init__(self, *,
                 course_id: int,
                 form_instance_id: int = 0,
                 request=None,
                 **kwargs) -> None:
        """
        :param course_id: ID of the course the form is associated with.
        :type course_id: int
        :param form_instance_id: ID of the form instance. Used to identify the form instance when
            saving its init parameters to the session and to reconstruct the form from the session.
            Defaults to 0. Should be set to a unique value when creating a new form instance within
            a single view with multiple instances of the same form class.
        :type form_instance_id: int
        :param request: HTTP request object received by the view the form is rendered in. Should be
            passed to the constructor if the form is instantiated with custom init parameters.
        :type request: HttpRequest
        :param kwargs: Additional keyword arguments to be passed to the :class:`CourseActionForm`
            super constructor.
        :type kwargs: dict
        """
        from main.views import RoleModelView

        super().__init__(form_instance_id=form_instance_id, request=request, **kwargs)

        self.fields['role'].data_source_url = RoleModelView.get_url(
            mode=RoleModelView.GetMode.FILTER,
            filter_params={'course': course_id}
        )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        """
        Adds the members from the CSV file to the course.

        :param request: POST request containing the CSV file.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, Any]
        """
        course = cls.get_context_course(request)

        role = int(request.POST.get('role'))

        fieldnames = ['Imię', 'Nazwisko', 'E-mail']
        file = CsvFileHandler(path=settings.UPLOAD_DIR,
                              file_data=request.FILES['members_csv'],
                              fieldnames=fieldnames)
        file.save()
        _fieldnames, members_to_add = file.read_csv(force_fieldnames=fieldnames,
                                                    ignore_first_line=True)
        file.validate()

        users_to_add = []
        for member in members_to_add:
            users_to_add.append(User.objects.get_or_create(
                email=member['E-mail'],
                first_name=member['Imię'],
                last_name=member['Nazwisko']
            ))
        course.add_members(users_to_add,
                           role,
                           ignore_errors=True)

        return {'message': _('Members added successfully')}

    @classmethod
    def is_permissible(cls, request) -> bool:
        """
        :param request: Request object.
        :type request: HttpRequest
        :return: `True` if the requesting user has the permission to add members to the course
            specified in the request, `False` otherwise. If the role specified in the request is the
            admin role, the user must have the `ADD_ADMIN` permission.
        :rtype: bool
        """
        course = cls.get_context_course(request)
        role = int(request.POST.get('role'))

        if role == course.admin_role.id:
            return request.user.has_course_permission(Course.CourseAction.ADD_ADMIN.label, course)

        return request.user.has_course_permission(cls.ACTION.label, course)


class AddMembersFromCSVFormWidget(FormWidget):
    """
    Form widget for the :class:`AddMembersFromCSVForm`.
    """

    def __init__(self,
                 request,
                 course_id: int,
                 form: AddMembersFromCSVForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param course_id: ID of the course the view this form widget is rendered in is associated
            with.
        :type course_id: int
        :param form: AddMembersFromCSVForm to be base the widget on. If not provided, a new form
            will be created.
        :type form: :class:`AddMembersFromCSVForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from main.views import CourseModelView

        if not form:
            form = AddMembersFromCSVForm(course_id=course_id, request=request)

        super().__init__(
            name='add_members_from_csv_form_widget',
            request=request,
            form=form,
            post_target_url=CourseModelView.post_url(**{'course_id': course_id}),
            button_text=_('Add members from CSV'),
            **kwargs
        )


# --------------------------------------- remove members --------------------------------------- #


class RemoveMembersForm(CourseActionForm):
    """
    Form for removing members from a course.
    """

    ACTION = Course.CourseAction.DEL_MEMBER

    #: Users to be removed from the course.
    members = TableSelectField(
        label=_('Choose members to remove'),
        table_widget_name='remove_members_table_widget',
        data_source_url='',
        cols=[TextColumn(name='email', header=_('Email')),
              TextColumn(name='first_name', header=_('First name')),
              TextColumn(name='last_name', header=_('Last name')),
              TextColumn(name='user_role', header=_('Role'))],
    )

    def __init__(self,
                 *,
                 course_id: int,
                 form_instance_id: int = 0,
                 request=None,
                 **kwargs) -> None:
        """
        :param course_id: ID of the course the form is associated with.
        :type course_id: int
        :param form_instance_id: ID of the form instance. Used to identify the form instance when
            saving its init parameters to the session and to reconstruct the form from the session.
            Defaults to 0. Should be set to a unique value when creating a new form instance within
            a single view with multiple instances of the same form class.
        :type form_instance_id: int
        :param request: HTTP request object received by the view the form is rendered in. Should be
            passed to the constructor if the form is instantiated with custom init parameters.
        :type request: HttpRequest
        :param kwargs: Additional keyword arguments to be passed to the :class:`CourseActionForm`
            super constructor.
        :type kwargs: dict
        """
        from main.views import UserModelView

        super().__init__(form_instance_id=form_instance_id, request=request, **kwargs)

        self.fields['members'].data_source_url = UserModelView.get_url(
            mode=UserModelView.GetMode.FILTER,
            filter_params={'roles__course': course_id},
            exclude_params={'id': request.user.id},
            serialize_kwargs={'course': course_id}
        )  # TODO: exclude admins

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Removes the users selected in the form from the course.

        :param request: POST request containing the form data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        :raises forms.ValidationError: If the request contains an attempt to remove an admin or the
            requesting user.
        """

        course = cls.get_context_course(request)
        users = TableSelectField.parse_value(request.POST.get('members'))

        if any([course.user_is_admin(user) for user in users]):
            raise forms.ValidationError(_('You cannot remove an admin from the course'))
        if any([user == request.user for user in users]):
            raise forms.ValidationError(_('You cannot remove yourself from the course'))

        course.remove_members(users)
        return {'message': _('Members removed successfully')}


class RemoveMembersFormWidget(FormWidget):
    """
    Form widget for the :class:`RemoveMembersForm`.
    """

    def __init__(self,
                 request,
                 course_id: int,
                 form: RemoveMembersForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param course_id: ID of the course the view this form widget is rendered in is associated
            with.
        :type course_id: int
        :param form: RemoveMembersForm to be base the widget on. If not provided, a new form will be
            created.
        :type form: :class:`RemoveMembersForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from main.views import CourseModelView

        if not form:
            form = RemoveMembersForm(course_id=course_id, request=request)

        super().__init__(
            name='remove_members_form_widget',
            request=request,
            form=form,
            post_target_url=CourseModelView.post_url(**{'course_id': course_id}),
            button_text=_('Remove members'),
            **kwargs
        )


# ============================================ ROLE ============================================ #

# ----------------------------------------- create role ---------------------------------------- #

class AddRoleForm(CourseActionForm):
    """
    Form for adding new :class:`main.Role` objects to a course.
    """

    ACTION = Course.CourseAction.ADD_ROLE

    #: Name of the new role.
    role_name = AlphanumericStringField(label=_('Role name'),
                                        required=True,
                                        min_length=4,
                                        max_length=Role._meta.get_field('name').max_length)

    #: Description of the new role.
    role_description = forms.CharField(label=_('Description'),
                                       required=False,
                                       widget=forms.Textarea(attrs={'rows': 3}))

    #: Permissions to be assigned to the new role.
    role_permissions = TableSelectField(label=_('Choose role permissions'),
                                        table_widget_name='role_permissions_table_widget',
                                        data_source_url='',
                                        cols=[TextColumn(name='codename', header=_('Codename')),
                                              TextColumn(name='name', header=_('Description'))],
                                        table_widget_kwargs={'table_height': 35})

    def __init__(self, **kwargs) -> None:
        from main.views import PermissionModelView

        super().__init__(**kwargs)

        self.fields['role_permissions'].data_source_url = PermissionModelView.get_url(
            mode=PermissionModelView.GetMode.FILTER,
            filter_params={'codename__in': Course.CourseAction.labels}
        )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Creates a new :class:`main.Role` object based on the data provided in the request and adds
        it to the course.

        :param request: POST request containing the form data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        course = cls.get_context_course(request)
        role_name = request.POST.get('role_name')
        role_description = request.POST.get('role_description', '')
        permissions = TableSelectField.parse_value(request.POST.get('role_permissions'))

        course.create_role(name=role_name, description=role_description, permissions=permissions)

        return {'message': _('Role ') + role_name + _(' created successfully')}


class AddRoleFormWidget(FormWidget):
    """
    Form widget for the :class:`AddRoleForm`.
    """

    def __init__(self,
                 request,
                 course_id: int,
                 form: AddRoleForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param course_id: ID of the course the view this form widget is rendered in is associated
            with.
        :type course_id: int
        :param form: AddRoleForm to be base the widget on. If not provided, a new form will be
            created.
        :type form: :class:`AddRoleForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from main.views import CourseModelView

        if not form:
            form = AddRoleForm()

        super().__init__(
            name='add_role_form_widget',
            request=request,
            form=form,
            post_target_url=CourseModelView.post_url(**{'course_id': course_id}),
            button_text=_('Add role'),
            **kwargs
        )


# ----------------------------------------- delete role ---------------------------------------- #

class DeleteRoleForm(CourseActionForm):
    """
    Form for deleting :class:`main.Role` records.
    """

    ACTION = Course.CourseAction.DEL_ROLE

    #: ID of the role to be deleted.
    role_id = forms.IntegerField(
        label=_('Role ID'),
        widget=forms.HiddenInput(attrs={'class': 'model-id', 'data-reset-on-refresh': 'true'}),
        required=True
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Deletes the role with the ID provided in the request.

        :param request: POST request containing the form data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        course = cls.get_context_course(request)
        role = ModelsRegistry.get_role(int(request.POST.get('role_id')))
        role_name = role.name
        course.remove_role(role)
        return {'message': _('Role ') + role_name + _(' deleted successfully')}


# ------------------------------------ add role permissions ------------------------------------ #

class AddRolePermissionsForm(CourseActionForm):
    ACTION = Course.CourseAction.EDIT_ROLE

    role_id = forms.IntegerField(label=_('Task ID'),
                                 widget=forms.HiddenInput(),
                                 required=True)

    # noinspection PyTypeChecker
    permissions_to_add = TableSelectField(
        label=_('Choose permissions to add'),
        table_widget_name='permissions_to_add_table_widget',
        data_source_url='',
        cols=[TextColumn(name='codename', header=_('Codename')),
              TextColumn(name='name', header=_('Description'))],
        table_widget_kwargs={'table_height': 35}
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        role = ModelsRegistry.get_role(int(request.POST.get('role_id')))
        perms = TableSelectField.parse_value(request.POST.get('permissions_to_add'))
        role.add_permissions(perms)
        return {'message': _('Permissions added successfully')}


class AddRolePermissionsFormWidget(FormWidget):
    def __init__(self,
                 *,
                 request,
                 course_id: int,
                 role_id: int,
                 form: AddRolePermissionsForm = None,
                 **kwargs) -> None:
        from main.views import CourseModelView, PermissionModelView

        if not form:
            form = AddRolePermissionsForm()

        codenames = Course.CourseAction.labels

        form.fields['permissions_to_add'].data_source_url = PermissionModelView.get_url(
            mode=PermissionModelView.GetMode.FILTER,
            filter_params={'codename__in': codenames},
            exclude_params={'role': role_id}
        )
        form.fields['role_id'].initial = role_id

        super().__init__(
            name='add_role_permissions_form_widget',
            request=request,
            form=form,
            post_target_url=CourseModelView.post_url(**{'course_id': course_id}),
            button_text=_('Add permissions'),
            **kwargs
        )


# ----------------------------------- remove role permissions ---------------------------------- #

class RemoveRolePermissionsForm(CourseActionForm):
    ACTION = Course.CourseAction.EDIT_ROLE

    role_id = forms.IntegerField(label=_('Task ID'),
                                 widget=forms.HiddenInput(),
                                 required=True)

    permissions_to_remove = TableSelectField(
        label=_('Choose permissions to remove'),
        table_widget_name='permissions_to_remove_table_widget',
        data_source_url='',
        cols=[TextColumn(name='codename', header=_('Codename')),
              TextColumn(name='name', header=_('Description'))],
        table_widget_kwargs={'table_height': 35}
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        role = ModelsRegistry.get_role(int(request.POST.get('role_id')))
        perms = TableSelectField.parse_value(request.POST.get('permissions_to_remove'))
        role.remove_permissions(perms)
        return {'message': _('Permissions removed successfully')}


class RemoveRolePermissionsFormWidget(FormWidget):
    def __init__(self,
                 *,
                 request,
                 course_id: int,
                 role_id: int,
                 form: RemoveRolePermissionsForm = None,
                 **kwargs) -> None:
        from main.views import CourseModelView, PermissionModelView

        if not form:
            form = RemoveRolePermissionsForm()

        form.fields['permissions_to_remove'].data_source_url = PermissionModelView.get_url(
            mode=PermissionModelView.GetMode.FILTER,
            filter_params={'role': role_id}
        )
        form.fields['role_id'].initial = role_id

        super().__init__(
            name='remove_role_permissions_form_widget',
            request=request,
            form=form,
            post_target_url=CourseModelView.post_url(**{'course_id': course_id}),
            button_text=_('Remove permissions'),
            **kwargs
        )


# ============================================ ROUND =========================================== #

# ---------------------------------------- create round ---------------------------------------- #

class CreateRoundForm(CourseModelForm):
    """
    Form for creating new :class:`course.Round` records.
    """

    MODEL = Round
    ACTION = Round.BasicAction.ADD

    #: Name of the new round.
    round_name = AlphanumericStringField(label=_('Round name'), required=True)
    #: Start date of the new round.
    start_date = DateTimeField(label=_('Start date'), required=True)
    #: End date of the new round.
    end_date = DateTimeField(label=_('End date'), required=False)
    #: Deadline date of the new round.
    deadline_date = DateTimeField(label=_('Deadline date'), required=True)
    #: Reveal date of the new round.
    reveal_date = DateTimeField(label=_('Reveal date'), required=False)

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Creates a new :class:`Round` record based on the data provided in the request.

        :param request: POST request containing the form data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        end_date = request.POST.get('end_date')
        reveal_date = request.POST.get('reveal_date')

        if not end_date:
            end_date = None
        if not reveal_date:
            reveal_date = None

        Round.objects.create_round(
            name=request.POST.get('round_name'),
            start_date=request.POST.get('start_date'),
            end_date=end_date,
            deadline_date=request.POST.get('deadline_date'),
            reveal_date=reveal_date
        )

        message = _('Round ') + request.POST.get('round_name') + _(' created successfully')
        return {'message': message}


class CreateRoundFormWidget(FormWidget):
    """
    Form widget for the :class:`CreateRoundForm`.
    """

    def __init__(self,
                 request,
                 course_id: int,
                 form: CreateRoundForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param course_id: ID of the course the view this form widget is rendered in is associated
            with.
        :type course_id: int
        :param form: CreateRoundForm to be base the widget on. If not provided, a new form will be
            created.
        :type form: :class:`CreateRoundForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from course.views import RoundModelView

        if not form:
            form = CreateRoundForm()

        super().__init__(
            name='create_round_form_widget',
            request=request,
            form=form,
            post_target_url=RoundModelView.post_url(**{'course_id': course_id}),
            button_text=_('Add round'),
            element_groups=[
                FormElementGroup(name='start_dates',
                                 elements=['start_date', 'reveal_date'],
                                 layout=FormElementGroup.FormElementsLayout.HORIZONTAL),
                FormElementGroup(name='end_dates',
                                 elements=['end_date', 'deadline_date'],
                                 layout=FormElementGroup.FormElementsLayout.HORIZONTAL)
            ],
            **kwargs
        )


# ----------------------------------------- edit round ----------------------------------------- #

class EditRoundForm(CourseModelForm):
    """
    Form for editing :class:`course.Round` records.
    """

    MODEL = Round
    ACTION = Round.BasicAction.EDIT

    #: Name of the round to be edited.
    round_name = AlphanumericStringField(label=_('Round name'), required=True)
    #: Start date of the round to be edited.
    start_date = DateTimeField(label=_('Start date'), required=True)
    #: End date of the round to be edited.
    end_date = DateTimeField(label=_('End date'), required=False)
    #: Deadline date of the round to be edited.
    deadline_date = DateTimeField(label=_('Deadline date'), required=True)
    #: Reveal date of the round to be edited.
    reveal_date = DateTimeField(label=_('Reveal date'), required=False)
    #: ID of the round to be edited.
    round_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self,
                 *,
                 course_id: int,
                 round_: int,
                 form_instance_id: int = 0,
                 request=None,
                 **kwargs) -> None:
        """
        :param course_id: ID of the course the form is associated with.
        :type course_id: int
        :param round_: ID of the round to be edited.
        :type round_: int
        :param form_instance_id: ID of the form instance. Used to identify the form instance when
            saving its init parameters to the session and to reconstruct the form from the session.
            Defaults to 0. Should be set to a unique value when creating a new form instance within
            a single view with multiple instances of the same form class.
        :type form_instance_id: int
        :param request: HTTP request object received by the view the form is rendered in. Should be
            passed to the constructor if the form is instantiated with custom init parameters.
        :type request: HttpRequest
        :param kwargs: Additional keyword arguments to be passed to the :class:`CourseModelForm`
            super constructor.
        :type kwargs: dict
        """
        super().__init__(form_instance_id=form_instance_id, request=request, **kwargs)

        round_obj = ModelsRegistry.get_round(round_, course_id)

        self.fields['round_name'].initial = round_obj.name
        self.fields['start_date'].initial = round_obj.start_date
        self.fields['end_date'].initial = round_obj.end_date
        self.fields['deadline_date'].initial = round_obj.deadline_date
        self.fields['reveal_date'].initial = round_obj.reveal_date
        self.fields['round_id'].initial = round_obj.pk

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Updates the :class:`Round` record with the ID provided in the request based on the submitted
        form data.

        :param request: POST request containing the form data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        round_ = ModelsRegistry.get_round(int(request.POST.get('round_id')))
        end_date = request.POST.get('end_date')
        reveal_date = request.POST.get('reveal_date')

        if not end_date:
            end_date = None
        if not reveal_date:
            reveal_date = None

        round_.update(
            name=request.POST.get('round_name'),
            start_date=request.POST.get('start_date'),
            end_date=end_date,
            deadline_date=request.POST.get('deadline_date'),
            reveal_date=reveal_date
        )

        message = _('Round ') + request.POST.get('round_name') + _(' edited successfully')
        return {'message': message}


class EditRoundFormWidget(FormWidget):
    """
    Form widget for the :class:`EditRoundForm`.
    """

    def __init__(self,
                 request,
                 course_id: int,
                 round_: int | Round,
                 form: EditRoundForm = None,
                 form_instance_id: int = 0,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param course_id: ID of the course the view this form widget is rendered in is associated
            with.
        :type course_id: int
        :param round_: ID of the round to be edited.
        :type round_: int
        :param form: EditRoundForm to be base the widget on. If not provided, a new form will be
            created.
        :type form: :class:`EditRoundForm`
        :param form_instance_id: ID of the form instance. Used to identify the form instance when
            saving its init parameters to the session and to reconstruct the form from the session.
            Defaults to 0. Should be set to a unique value when creating a new form instance within
            a single view with multiple instances of the same form class.
        :type form_instance_id: int
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from course.views import RoundModelView

        if isinstance(round_, Round):
            round_pk = round_.pk
        else:
            round_pk = round_

        if not form:
            form = EditRoundForm(course_id=course_id,
                                 round_=round_pk,
                                 form_instance_id=form_instance_id,
                                 request=request)

        round_obj = ModelsRegistry.get_round(round_, course_id)

        super().__init__(
            name=f'edit_round{round_obj.pk}_form_widget',
            request=request,
            form=form,
            post_target_url=RoundModelView.post_url(**{'course_id': course_id}),
            button_text=f"{_('Edit round')} {round_obj.name}",
            element_groups=[
                FormElementGroup(name='start_dates',
                                 elements=['start_date', 'reveal_date'],
                                 layout=FormElementGroup.FormElementsLayout.HORIZONTAL),
                FormElementGroup(name='end_dates',
                                 elements=['end_date', 'deadline_date'],
                                 layout=FormElementGroup.FormElementsLayout.HORIZONTAL)
            ],
            **kwargs
        )


# ---------------------------------------- delete round ---------------------------------------- #

class DeleteRoundForm(CourseModelForm):
    """
    Form for deleting existing :class:`course.Round` objects.
    """

    MODEL = Round
    ACTION = Round.BasicAction.DEL

    #: ID of the round to be deleted.
    round_id = forms.IntegerField(
        label=_('Round ID'),
        widget=forms.HiddenInput(attrs={'class': 'model-id', 'data-reset-on-refresh': 'true'}),
        required=True,
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        """
        Deletes the round with the ID provided in the request.

        :param request: POST request containing the round ID.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, Any]
        """
        Round.objects.delete_round(int(request.POST.get('round_id')))
        return {'message': _('Round deleted successfully')}


# ============================================ TASK ============================================ #

# ----------------------------------------- create task ---------------------------------------- #

class CreateTaskForm(CourseModelForm):
    """
    Form for creating new :class:`course.Task` records.
    """

    MODEL = Task
    ACTION = Task.BasicAction.ADD

    #: Name of the new task.
    task_name = AlphanumericStringField(
        label=_('Task name'),
        help_text=_('If not provided - task name will be taken from package.'),
        required=False,
    )

    #: Round the new task is assigned to.
    round_ = ModelChoiceField(
        data_source_url='',
        label_format_string='[[name]] ([[f_start_date]] - [[f_deadline_date]])',
        label=_('Round'),
        required=True,
    )

    #: Point value of the new task.
    points = forms.FloatField(label=_('Points'),
                              min_value=0,
                              required=False,
                              help_text=_('If not provided - points will be taken from package.'))

    # noinspection PyTypeChecker
    #: Package containing the new task's definition.
    package = FileUploadField(label=_('Task package'),
                              allowed_extensions=['zip'],
                              required=True,
                              help_text=_('Only .zip files are allowed'))

    #: Judging mode of the new task.
    judge_mode = ChoiceField(label=_('Judge mode'),
                             choices=TaskJudgingMode,
                             required=True,
                             placeholder_default_option=False)

    def __init__(self,
                 *,
                 course_id: int,
                 form_instance_id: int = 0,
                 request=None,
                 **kwargs) -> None:
        """
        :param course_id: ID of the course the form is associated with.
        :type course_id: int
        :param form_instance_id: ID of the form instance. Used to identify the form instance when
            saving its init parameters to the session and to reconstruct the form from the session.
            Defaults to 0. Should be set to a unique value when creating a new form instance within
            a single view with multiple instances of the same form class.
        :type form_instance_id: int
        :param request: HTTP request object received by the view the form is rendered in. Should be
            passed to the constructor if the form is instantiated with custom init parameters.
        :type request: HttpRequest
        :param kwargs: Additional keyword arguments to be passed to the :class:`CourseModelForm`
            super constructor.
        :type kwargs: dict
        """
        from course.views import RoundModelView

        super().__init__(form_instance_id=form_instance_id, request=request, **kwargs)

        self.fields['round_'].data_source_url = RoundModelView.get_url(
            serialize_kwargs={'add_formatted_dates': True},
            **{'course_id': course_id}
        )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Creates a new :class:`Task` object based on the data provided in the request.
        Also creates a new :class:`PackageSource` and :class:`PackageInstance` objects based on the
        uploaded package.

        :param request: POST request containing the task data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        from package.models import PackageSource

        task_name = request.POST.get('task_name')
        round_id = int(request.POST.get('round_'))
        points = request.POST.get('points')
        judge_mode = request.POST.get('judge_mode')
        if judge_mode is None:
            judge_mode = TaskJudgingMode.LIN
        else:
            judge_mode = TaskJudgingMode[judge_mode]
        file = FileHandler(settings.UPLOAD_DIR, 'zip', request.FILES['package'])
        file.save()
        try:
            package_instance = PackageSource.objects.create_package_source_from_zip(
                name=task_name,
                zip_file=file.path,
                creator=request.user,
                return_package_instance=True
            )
            Task.objects.create_task(
                package_instance=package_instance,
                round_=round_id,
                task_name=task_name,
                points=points,
                judging_mode=judge_mode,
            )
        except Exception as e:
            file.delete()
            raise e
        file.delete()
        return {'message': _('Task ') + task_name + _(' created successfully')}


class CreateTaskFormWidget(FormWidget):
    """
    Form widget for the :class:`CreateTaskForm`.
    """

    def __init__(self,
                 request,
                 course_id: int,
                 form: CreateTaskForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param course_id: ID of the course the view this form widget is rendered in is associated
            with.
        :type course_id: int
        :param form: CreateTaskForm to be base the widget on. If not provided, a new form will be
            created.
        :type form: :class:`CreateTaskForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from course.views import TaskModelView

        if not form:
            form = CreateTaskForm(course_id=course_id, request=request)

        super().__init__(
            name='create_task_form_widget',
            request=request,
            form=form,
            post_target_url=TaskModelView.post_url(**{'course_id': course_id}),
            button_text=_('Add task'),
            element_groups=FormElementGroup(name='grading',
                                            elements=['points', 'judge_mode'],
                                            layout=FormElementGroup.FormElementsLayout.HORIZONTAL),
            **kwargs
        )


# ----------------------------------------- delete task ---------------------------------------- #


class DeleteTaskForm(CourseModelForm):
    """
    Form for deleting :class:`course.Task` records.
    """

    MODEL = Task
    ACTION = Task.BasicAction.DEL

    #: ID of the task to be deleted.
    task_id = forms.IntegerField(
        label=_('Task ID'),
        widget=forms.HiddenInput(attrs={'class': 'model-id', 'data-reset-on-refresh': 'true'}),
        required=True,
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Deletes the task with the ID provided in the request.

        :param request: POST request containing the task ID.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        Task.objects.delete_task(int(request.POST.get('task_id')))
        return {'message': _('Task deleted successfully')}


class DeleteTaskFormWidget(FormWidget):
    """
    Form widget for deleting tasks.

    See also:
        - :class:`FormWidget`
        - :class:`DeleteTaskForm`
    """

    def __init__(self,
                 request,
                 course_id: int,
                 form: DeleteTaskForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param course_id: ID of the course the view this form widget is rendered in is associated
            with.
        :type course_id: int
        :param form: Form to be base the widget on. If not provided, a new form will be created.
        :type form: :class:`DeleteTaskForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        from course.views import TaskModelView

        if not form:
            form = DeleteTaskForm()

        super().__init__(
            name='delete_task_form_widget',
            request=request,
            form=form,
            post_target_url=TaskModelView.post_url(**{'course_id': course_id}),
            button_text=_('Delete task'),
            submit_confirmation_popup=SubmitConfirmationPopup(
                title=_('Confirm task deletion'),
                message=_(
                    'Are you sure you want to delete this task? This action cannot be undone.'
                ),
                confirm_button_text=_('Delete task'),
            ),
            **kwargs
        )


# ----------------------------------------- edit task ------------------------------------------ #

class EditTaskForm(CourseModelForm):
    """
    Form for editing :class:`course.Task` records.
    """

    MODEL = Task
    ACTION = Task.BasicAction.EDIT

    task_title = AlphanumericStringField(label=_('Task title'), required=True)
    round_ = ModelChoiceField(
        label_format_string='[[name]] ([[f_start_date]] - [[f_deadline_date]])',
        label=_('Round'),
        required=True,
    )
    task_judge_mode = ChoiceField(label=_('Task judge mode'),
                                  choices=TaskJudgingMode,
                                  required=True)

    # package settings
    task_points = forms.FloatField(label=_('Task points'), required=False)
    memory_limit = forms.CharField(label=_('Memory limit'), required=False)
    # TODO: add memory amount field (low prio)
    time_limit = forms.FloatField(label=_('Time limit [s]'), required=False)

    # TODO: multi select field
    allowed_extensions = forms.CharField(label=_('Allowed extensions'), required=False)
    cpus = forms.IntegerField(label=_('CPUs'), required=False)

    def add_field(self, fields: List[str], field: forms.Field, name: str) -> None:
        fields.append(name)
        self.fields[name] = field

    def __init__(self, *,
                 course_id: int,
                 task_id: int,
                 form_instance_id: int = 0,
                 request=None,
                 **kwargs) -> None:
        from course.views import RoundModelView

        super().__init__(form_instance_id=form_instance_id, request=request, **kwargs)

        self.fields['round_'].data_source_url = RoundModelView.get_url(
            serialize_kwargs={'add_formatted_dates': True},
            **{'course_id': course_id}
        )
        course = ModelsRegistry.get_course(course_id)
        task = course.get_task(task_id)
        package = task.package_instance.package

        # initials
        self.fields['task_title'].initial = task.task_name
        # TODO: model choice field need to support initial value
        self.fields['task_judge_mode'].initial = task.judging_mode
        self.fields['task_points'].initial = task.points
        self.fields['memory_limit'].initial = package['memory_limit']
        self.fields['time_limit'].initial = package['time_limit']
        self.fields['allowed_extensions'].initial = ', '.join(package['allowedExtensions'])
        self.fields['cpus'].initial = package['cpus']

        self.general_fields = list(self.fields.keys())

        self.set_groups = []
        # test sets
        for t_set in task.sets:
            package_ts = package.sets(t_set.short_name)
            set_fields = []
            set_group = {'name': t_set.short_name}

            t_set_name = AlphanumericStringField(
                label=_('Test set name'),
                required=True,
                initial=t_set.short_name
            )
            self.add_field(fields=set_fields, field=t_set_name, name=f'ts_{t_set.pk}_name')

            t_set_weight = forms.FloatField(
                label=_('Test set weight'),
                required=True,
                initial=t_set.weight
            )
            self.add_field(fields=set_fields, field=t_set_weight, name=f'ts_{t_set.pk}_weight')

            # TODO: add memory amount field (low prio)
            t_set_memory_limit = forms.CharField(
                label=_('Memory limit'),
                required=True,
                initial=package_ts['memory_limit']
            )
            self.add_field(fields=set_fields, field=t_set_memory_limit,
                           name=f'ts_{t_set.pk}_memory_limit')

            t_set_time_limit = forms.FloatField(
                label=_('Time limit [s]'),
                required=True,
                initial=package_ts['time_limit']
            )
            self.add_field(fields=set_fields, field=t_set_time_limit,
                           name=f'ts_{t_set.pk}_time_limit')

            set_group['fields'] = set_fields
            test_groups = []

            # single tests
            for test in t_set.tests:
                package_ts_t = package_ts.tests(test.short_name)
                test_group = {'name': test.short_name}
                test_fields = []

                t_set_t_name = AlphanumericStringField(
                    label=_('Test name'),
                    required=True,
                    initial=test.short_name
                )
                self.add_field(fields=test_fields, field=t_set_t_name,
                               name=f'ts_{t_set.pk}_t_{test.pk}_name')

                # TODO: add memory amount field (low prio)
                t_set_t_memory_limit = forms.CharField(
                    label=_('Memory limit'),
                    required=True,
                    initial=package_ts_t['memory_limit']
                )
                self.add_field(fields=test_fields, field=t_set_t_memory_limit,
                               name=f'ts_{t_set.pk}_t_{test.pk}_memory_limit')

                t_set_t_time_limit = forms.FloatField(
                    label=_('Time limit [s]'),
                    required=True,
                    initial=package_ts_t['time_limit']
                )
                self.add_field(fields=test_fields, field=t_set_t_time_limit,
                               name=f'ts_{t_set.pk}_t_{test.pk}_time_limit')

                t_set_t_input = FileUploadField(
                    label=_('Change input file'),
                    allowed_extensions=['in'],
                    required=False,
                )
                self.add_field(fields=test_fields, field=t_set_t_input,
                               name=f'ts_{t_set.pk}_t_{test.pk}_input')

                t_set_t_output = FileUploadField(
                    label=_('Change output file'),
                    allowed_extensions=['out'],
                    required=False,
                )
                self.add_field(fields=test_fields, field=t_set_t_output,
                               name=f'ts_{t_set.pk}_t_{test.pk}_output')

                test_group['fields'] = test_fields
                test_groups.append(test_group)

            set_group['test_groups'] = test_groups
            self.set_groups.append(set_group)

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        logger.error(f'Not implemented. Request.POST: \n{request.POST}')
        raise NotImplementedError('Not implemented')


class EditTaskFormWidget(FormWidget):
    """
    This class is a form widget for the :class:`EditTaskForm`.
    """

    def __init__(self,
                 request,
                 course_id: int,
                 task_id: int | None = None,
                 form: EditTaskForm = None,
                 **kwargs) -> None:
        """
        :param request: The HTTP request object received by the view this form widget
            is rendered in.
        :type request: HttpRequest
        :param course_id: The ID of the course the view this form widget is rendered in
            is associated with.
        :type course_id: int
        :param task_id: The ID of the task to be edited. If not provided,
            a new form will be created.
        :type task_id: int, optional
        :param form: The EditTaskForm to be base the widget on. If not provided,
            a new form will be created.
        :type form: EditTaskForm, optional
        """
        from course.views import TaskModelView

        if not form:
            if not task_id:
                raise ValueError('Task ID must be provided when creating a new task form')

            form = EditTaskForm(course_id=course_id,
                                request=request,
                                task_id=task_id)

        element_groups = self._create_element_groups(form)

        super().__init__(
            name='edit_task_form_widget',
            request=request,
            form=form,
            post_target_url=TaskModelView.post_url(**{'course_id': course_id}),
            element_groups=element_groups,
            button_text=_('Edit task'),
            form_observer=self._create_form_observer(form),
            **kwargs
        )

    def _create_element_groups(self, form: EditTaskForm) -> List[FormElementGroup]:
        general_fields = form.general_fields.copy()
        judge_mode_field = self._extract_field_name(general_fields, 'task_judge_mode')
        points_field = self._extract_field_name(general_fields, 'task_points')
        memory_limit_field = self._extract_field_name(general_fields, 'memory_limit')
        time_limit_field = self._extract_field_name(general_fields, 'time_limit')
        cpus_field = self._extract_field_name(general_fields, 'cpus')
        extension_field = self._extract_field_name(general_fields, 'allowed_extensions')

        grading_group = FormElementGroup(
            elements=[judge_mode_field, points_field],
            name='grading-settings',
            layout=FormElementGroup.FormElementsLayout.HORIZONTAL
        )

        limit_group = FormElementGroup(
            elements=[memory_limit_field, time_limit_field, cpus_field],
            name='limits-settings',
            layout=FormElementGroup.FormElementsLayout.HORIZONTAL
        )

        general_elements = general_fields + [grading_group, limit_group, extension_field]
        element_groups = [FormElementGroup(elements=general_elements,
                                           name='general-settings',
                                           title=_('General settings'),
                                           layout=FormElementGroup.FormElementsLayout.VERTICAL)]

        for set_group in form.set_groups:
            set_group_fields = set_group['fields'].copy()
            name_field = self._extract_field_name(set_group_fields, 'name')
            weight_field = self._extract_field_name(set_group_fields, 'weight')
            memory_limit_field = self._extract_field_name(set_group_fields, 'memory_limit')
            time_limit_field = self._extract_field_name(set_group_fields, 'time_limit')

            base_group = FormElementGroup(
                elements=[name_field, weight_field],
                name=f'{set_group["name"]}-base',
                layout=FormElementGroup.FormElementsLayout.HORIZONTAL
            )

            limit_group = FormElementGroup(
                elements=[memory_limit_field, time_limit_field],
                name=f'{set_group["name"]}-limits',
                layout=FormElementGroup.FormElementsLayout.HORIZONTAL
            )

            element_groups.append(
                FormElementGroup(elements=set_group_fields + [base_group, limit_group],
                                 name=f'{set_group["name"]}-settings',
                                 title=set_group['name'],
                                 layout=FormElementGroup.FormElementsLayout.VERTICAL,
                                 frame=True)
            )

            for test_group in set_group['test_groups']:
                test_group_fields = test_group['fields'].copy()
                memory_limit_field = self._extract_field_name(test_group_fields, 'memory_limit')
                time_limit_field = self._extract_field_name(test_group_fields, 'time_limit')
                input_field = self._extract_field_name(test_group_fields, 'input')
                output_field = self._extract_field_name(test_group_fields, 'output')

                limit_group = FormElementGroup(
                    elements=[memory_limit_field, time_limit_field],
                    name=f'{test_group["name"]}-limits',
                    layout=FormElementGroup.FormElementsLayout.HORIZONTAL
                )

                file_group = FormElementGroup(
                    elements=[input_field, output_field],
                    name=f'{test_group["name"]}-files',
                    layout=FormElementGroup.FormElementsLayout.HORIZONTAL
                )

                element_groups.append(
                    FormElementGroup(elements=test_group_fields + [limit_group, file_group],
                                     name=test_group['name'],
                                     title=test_group['name'],
                                     layout=FormElementGroup.FormElementsLayout.VERTICAL,
                                     frame=True)
                )

        return element_groups

    @staticmethod
    def _create_form_observer(form: EditTaskForm) -> FormObserver:
        tabs = []

        for set_group in form.set_groups:
            fields = set_group['fields']

            for test_group in set_group['test_groups']:
                fields += test_group['fields']

            tabs.append(FormObserverTab(name=set_group['name'],
                                        title=set_group['name'],
                                        fields=fields))

        return FormObserver(tabs=tabs)

    @staticmethod
    def _extract_field_name(fields: List[str], name: str) -> str:
        field_name = next((f for f in fields if name in f), None)

        if field_name is None:
            raise ValueError(f'Field with name {name} not found in provided field names list')

        fields.remove(field_name)
        return field_name

    def get_sidenav(self, request) -> SideNav:
        sidenav = SideNav(request=request,
                          collapsed=True,
                          tabs=['General settings'],
                          toggle_button=True)
        set_groups = getattr(self.form, 'set_groups', [])

        for test_set in set_groups:
            sidenav.add_tab(
                tab_name=test_set['name'],
                sub_tabs=[f'{test_set["name"]} settings'] +
                         [test_set_test['name'] for test_set_test in test_set['test_groups']]
            )

        return sidenav


# ========================================= SUBMISSION ========================================= #

# -------------------------------------- create submission ------------------------------------- #

class CreateSubmitForm(CourseModelForm):
    """
    Form for creating new :class:`course.Submit` records.
    """

    MODEL = Submit
    ACTION = Submit.BasicAction.ADD

    # noinspection PyTypeChecker
    #: Source code of the new submission.
    source_code = FileUploadField(label=_('Source code'), required=True)
    #: ID of the task the new submission is for.
    task_id = forms.IntegerField(label=_('Task ID'), widget=forms.HiddenInput(), required=True)

    def __init__(self,
                 *,
                 course_id: int,
                 task_id: int,
                 form_instance_id: int = 0,
                 request=None,
                 **kwargs) -> None:
        """
        :param course_id: ID of the course the form is associated with.
        :type course_id: int
        :param task_id: ID of the task the submission is for.
        :type task_id: int
        :param form_instance_id: ID of the form instance. Used to identify the form instance when
            saving its init parameters to the session and to reconstruct the form from the session.
            Defaults to 0. Should be set to a unique value when creating a new form instance within
            a single view with multiple instances of the same form class.
        :type form_instance_id: int
        :param request: HTTP request object received by the view the form is rendered in. Should be
            passed to the constructor if the form is instantiated with custom init parameters.
        :type request: HttpRequest
        :param kwargs: Additional keyword arguments to be passed to the :class:`CourseModelForm`
            super constructor.
        :type kwargs: dict
        """
        super().__init__(form_instance_id=form_instance_id, request=request, **kwargs)

        self.fields['task_id'].initial = task_id
        if settings.MOCK_BROKER:
            self.fields['result_types'] = forms.MultipleChoiceField(
                choices=ResultStatus.choices,
                initial=[ResultStatus.OK, ResultStatus.ANS, ResultStatus.TLE, ResultStatus.MEM],
                help_text=_(
                    'Mocking broker is enabled. No submissions will be sent to the broker.'),
                required=False
            )
        course = ModelsRegistry.get_course(course_id)
        task = course.get_task(task_id)
        allowed_extensions = task.package_instance.package['allowedExtensions']
        self.fields['source_code'].help_text = (
            f'{_("Allowed extensions:")} [{", ".join(allowed_extensions)}] '
            f'{_("and zips containing these files")}'
        )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Creates a new :class:`Submit` object based on the data provided in the request.

        :param request: POST request containing the form data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        file_extension = request.FILES['source_code'].name.split('.')[-1]
        source_code_file = FileHandler(settings.SUBMITS_DIR,
                                       file_extension,
                                       request.FILES['source_code'])
        source_code_file.save()
        task_id = int(request.POST.get('task_id'))
        task = ModelsRegistry.get_task(task_id)
        if not task:
            source_code_file.delete()
            raise ValueError('Task not found')

        task.package_instance.package.check_source(source_code_file.path)

        user = request.user

        available_statuses = None
        if settings.MOCK_BROKER:
            available_statuses = request.POST.getlist('result_types')
            available_statuses = [ResultStatus[status] for status in available_statuses]

        try:
            Submit.objects.create_submit(
                source_code=source_code_file.path,
                task=task_id,
                user=user,
                auto_send=True,
                available_statuses=available_statuses,
            )
        except Exception as e:
            source_code_file.delete()
            raise e
        return {'message': _('Submit created successfully')}


class CreateSubmitFormWidget(FormWidget):
    """
    Form widget for the :class:`CreateSubmitForm`.
    """

    def __init__(self,
                 request,
                 course_id: int,
                 task_id: int | None = None,
                 form: CreateTaskForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param course_id: ID of the course the view this form widget is rendered in is associated
            with.
        :type course_id: int
        :param task_id: ID of the task the submission is for.
        :type task_id: int
        :param form: CreateSubmitForm to be base the widget on. If not provided, a new form will be
            created.
        :type form: :class:`CreateSubmitForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        :raises ValueError: If the task ID is not provided when creating a new form.
        """
        from course.views import SubmitModelView

        if not form and not task_id:
            raise ValueError('Task ID must be provided when creating a new submit form')

        if not form:
            form = CreateSubmitForm(course_id=course_id,
                                    task_id=task_id,
                                    request=request)

        super().__init__(
            name='create_submit_form_widget',
            request=request,
            form=form,
            post_target_url=SubmitModelView.post_url(**{'course_id': course_id}),
            button_text=_('New submission'),
            **kwargs
        )
