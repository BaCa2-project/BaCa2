Main app
========

.. autoclass:: main.models.UserManager
    :members: create_user, create_superuser
    :private-members: _create_user


.. autoclass:: main.models.Course
    :members: name, short_name, db_name, add_user
    :special-members: __str__


.. autoclass:: main.models.User
    :members:
        email, username, is_staff, is_superuser, first_name, last_name, date_joined,
        USERNAME_FIELD, EMAIL_FIELD, REQUIRED_FIELDS, objects,
        exists, can_access_course, check_general_permissions, check_course_permissions


.. autoclass:: main.models.GroupCourse
    :members: group, course


.. autoclass:: main.models.UserCourse
    :members: user, course, group_course

