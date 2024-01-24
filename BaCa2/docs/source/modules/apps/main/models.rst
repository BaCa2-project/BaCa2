Models
======

Main models are divided into 3 groups:

1. User related models: ``UserManager``, ``User``, ``Settings``
2. Permission management: ``RoleManager``, ``Role``, ``RolePresetManager``, ``RolePreset``, ``RolePresetUser``
3. Course control models: ``CourseManager``, ``Course``

User related models
"""""""""""""""""""

.. autoclass:: main.models.UserManager
    :members:
    :private-members:

.. autoclass:: main.models.User
    :members:
    :private-members:

.. autoclass:: main.models.Settings
    :members:
    :private-members:

Permission management
"""""""""""""""""""""

.. autoclass:: main.models.RoleManager
    :members:
    :private-members:

.. autoclass:: main.models.Role
    :members:
    :private-members:

.. autoclass:: main.models.RolePresetManager
    :members:
    :private-members:

.. autoclass:: main.models.RolePreset
    :members:
    :private-members:

.. autoclass:: main.models.RolePresetUser
    :members:
    :private-members:

Course control models
"""""""""""""""""""""

.. autoclass:: main.models.CourseManager
    :members:
    :private-members:

.. autoclass:: main.models.Course
    :members:
    :exclude-members: Round, Task, Submit
    :private-members:
