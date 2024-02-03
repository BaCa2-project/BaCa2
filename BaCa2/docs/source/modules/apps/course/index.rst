Course app
==========

Course app is a template-like app, used to create and manage courses. Course is set up as a separated database,
so Course models have to use ``InCourse`` or ``OptionalInCourse`` decorators, to be accessed properly.

Course app is divided into 3 parts:

1. Manager - provides methods to create and delete courses.
2. Routing - defines ``ContextCourseRouter`` used to route requests to proper course database. Also defines ``InCourse`` and ``OptionalInCourse`` decorators, used to access course models.
3. Models - defines ``Course`` models, which are used to store information about courses.

.. toctree::
    :maxdepth: 2
    :caption: Components:

    manager
    routing
    models
    views
