Views module
------------

The Views module of ``main`` app contains abstract definition of project View (``BaCa2ModelView``) and definitions
for other main views, related with models from ``main`` app. Also login and dashboard views are defined here.

Model-related views
"""""""""""""""""""

.. autoclass:: main.views.BaCa2ModelView
    :members:
    :private-members:

.. autoclass:: main.views.UserModelView
    :members:
    :private-members:

.. autoclass:: main.views.CourseModelView
    :members:
    :private-members:

Authentication views
""""""""""""""""""""

.. autoclass:: main.views.BaCa2LoginView
    :members:
    :private-members:

.. autoclass:: main.views.BaCa2LogoutView
    :members:
    :private-members:

Admin views
"""""""""""

.. autoclass:: main.views.AdminView
    :members:
    :private-members:

Application views
"""""""""""""""""

.. autoclass:: main.views.DashboardView
    :members:
    :private-members:

.. autoclass:: main.views.CoursesView
    :members:
    :private-members:

Management functions
""""""""""""""""""""

.. automodule:: main.views
    :members: change_theme

