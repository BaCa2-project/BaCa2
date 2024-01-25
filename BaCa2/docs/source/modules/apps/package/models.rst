.. module:: package.models

Models
------

Are divided into 2 categories:

1. Package management - models that are used to manage packages
2. Package access - models that are used to setup and control who can access packages


Package Management
""""""""""""""""""

.. autoclass:: PackageSourceManager
   :members:
   :private-members:

.. autoclass:: PackageSource
   :members:
   :private-members:

.. autoclass:: PackageInstanceManager
    :members:
    :private-members:

.. autoclass:: PackageInstance
    :members:
    :private-members:


Package Access
""""""""""""""

.. autoclass:: PackageInstanceUserManager
    :members:
    :private-members:

.. autoclass:: PackageInstanceUser
    :members:
    :private-members:
