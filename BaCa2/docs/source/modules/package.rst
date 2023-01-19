Package
=======


Models
------

.. autoclass:: package.models.PackageSource
    :members: path

.. autoclass:: package.models.PackageInstance
    :members: key, package, path, create_from_me, delete_instance, share

.. autoclass:: package.models.PackageInstanceUser

Package Manager
---------------

.. autofunction:: package.package_manage.merge_settings

.. autoclass:: package.package_manage.PackageManager
    :members:
    :special-members: __init__, __getitem__, __setitem__

.. autoclass:: package.package_manage.Package
    :members:

.. autoclass:: package.package_manage.TSet
    :members:

.. autoclass:: package.package_manage.TestF
    :members:

Validators
----------

.. automodule:: package.validators
    :members:

