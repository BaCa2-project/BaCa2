Course
======

Course structure is based on 3 main parts:

1. Django models

2. Django router and context manager

3. Dynamic database creator


Models
------

.. autoclass:: course.models.Round
    :members: start_date, end_date, deadline_date, reveal_date, validate

.. autoclass:: course.models.Task
    :members: package_instance_id, task_name, round, judging_mode, points, create_new, sets, package_instance,
        last_submit, best_submit, check_instance

.. autoclass:: course.models.TestSet
    :members: task, short_name, weight, tests

.. autoclass:: course.models.Submit
    :members: submit_date, source_code, task, usr, final_score, create_new, user, score

.. autoclass:: course.models.Result
    :members: test, submit, status

DB Router
---------

.. autoclass:: course.routing.SimpleCourseRouter
    :members:

.. autoclass:: course.routing.ContextCourseRouter
    :members:
    :private-members: _get_context

.. autoclass:: course.routing.InCourse
    :members:


Dynamic DB creator
------------------

Course manager
..............

To simplify usage there is a module :py:mod:`course.manager`. It gives away 2 functions described below.

.. automodule:: course.manager
    :members:

DB creator
..........

Course manager module uses functions from :py:mod:`BaCa2.db.creator`.

.. important::
    Managing actions are in critical section. Multithread access may crush the application. That's why following lock
    is used:


    .. automodule:: BaCa2.db.creator
        :private-members: _db_root_access

    Only 2 functions need to acquire that lock.

Finally these functions are given out by creator module:

.. automodule:: BaCa2.db.creator
    :members:
