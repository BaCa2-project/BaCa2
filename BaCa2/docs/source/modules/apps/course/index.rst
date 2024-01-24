Course app
==========

Course app is a template-like app, used to create and manage courses. Course is set up as a separated database,
so Course models have to use ``InCourse`` or ``OptionalInCourse`` decorators, to be accessed properly.

Course app is divided into 3 parts:

1. Manager - provides methods to create and delete courses.
2. Routing - defines ``ContextCourseRouter`` used to route requests to proper course database. Also defines ``InCourse`` and ``OptionalInCourse`` decorators, used to access course models.
3. Models - defines ``Course`` models, which are used to store information about courses.

Manager
"""""""

.. automodule:: course.manager
    :members:

Routing
"""""""

.. autoclass:: course.routing.ContextCourseRouter
    :members:
    :private-members: _get_context
    :inherited-members:

.. autoclass:: course.routing.InCourse
    :members:

.. autoclass:: course.routing.OptionalInCourse
    :members:
