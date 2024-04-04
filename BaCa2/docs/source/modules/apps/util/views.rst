.. module:: util.views

Views
-----

Util app does not posses any views directly accessible by the user. Instead, its view module stores commonly used abstract base classes for other apps to use in their class-based views. It also stores the ``BaCa2ContextMixin`` class which all template views across the project inherit from.

.. autoclass:: BaCa2ContextMixin
    :members:
    :private-members:

.. autoclass:: BaCa2ModelView
    :members:
    :private-members:

.. autoclass:: BaCa2LoggedInView
    :members:
    :private-members:

.. autoclass:: FieldValidationView
    :members:
    :private-members:
