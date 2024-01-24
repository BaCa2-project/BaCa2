.. module:: main.models

Models
======

Main models are divided into 3 groups:

1. User related models: ``UserManager``, ``User``, ``Settings``
2. Permission management: ``RoleManager``, ``Role``, ``RolePresetManager``, ``RolePreset``, ``RolePresetUser``
3. Course control models: ``CourseManager``, ``Course``

User related models
"""""""""""""""""""

.. autoclass:: UserManager
    :members:
    :private-members:

.. autoclass:: User
    :members:
    :private-members:

.. autoclass:: Settings
    :members:
    :private-members:

Permission management
"""""""""""""""""""""

.. autoclass:: RoleManager
    :members:
    :private-members:

.. autoclass:: Role
    :members:
    :private-members:

.. autoclass:: RolePresetManager
    :members:
    :private-members:

.. autoclass:: RolePreset
    :members:
    :private-members:

.. autoclass:: RolePresetUser
    :members:
    :private-members:

Course control models
"""""""""""""""""""""

.. autoclass:: CourseManager
    :members:
    :private-members:

.. autoclass:: Course
    :members:
    :exclude-members: Round, Task, Submit
    :private-members:
