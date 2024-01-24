.. module:: main.views

Views
-----

The Views module of ``main`` app contains abstract definition of project View (``BaCa2ModelView``) and definitions
for other main views, related with models from ``main`` app. Also login and dashboard views are defined here.

Model-related views
"""""""""""""""""""

.. autoclass:: UserModelView
    :members:
    :private-members:

.. autoclass:: CourseModelView
    :members:
    :private-members:

Authentication views
""""""""""""""""""""

.. autoclass:: BaCa2LoginView
    :members:
    :private-members:

.. autoclass:: BaCa2LogoutView
    :members:
    :private-members:

Admin views
"""""""""""

.. autoclass:: AdminView
    :members:
    :private-members:

Application views
"""""""""""""""""

.. autoclass:: DashboardView
    :members:
    :private-members:

.. autoclass:: CoursesView
    :members:
    :private-members:

Management functions
""""""""""""""""""""

.. autofunction:: change_theme

