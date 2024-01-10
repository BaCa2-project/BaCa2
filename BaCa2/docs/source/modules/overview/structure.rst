Application structure
=====================

The BaCa2 application structure is divided into three main parts:

    1. Django web application
    2. BaCa2-broker (communication backend)
    3. Package manager

While Django app and Package manager are crucial for proper operation of the app,
Broker is open to be changed. BaCa2-broker is fully functional app, providing communication
between BaCa2 web app and `KOLEJKA <https://kolejka.matinf.uj.edu.pl/>`_ task checking service.

Django web application
----------------------

.. image:: ../../_static/gh_icon.svg
    :target: https://github.com/BaCa2-project/BaCa2

This Django-based web app is designed to provide an online platform for creating and managing programming tasks,
as well as submitting solutions for automatic evaluation. The system revolves around the concept of courses which are
used to organize groups of users into roles and provide them with access to a curated list of tasks designed
by course leaders.

Currently developed for the `Institute of Computer Science and Mathematics <https://matinf.uj.edu.pl/>`_ at
the Jagiellonian University

Inner structure
'''''''''''''''

The Django project is organized into three main apps:

1. ``main`` - responsible for authentication, user data and settings, management of courses and their members
2. ``course`` - responsible for management of tasks, submissions and other data and functionalities internal to any given course
3. ``package`` - used to communicate with BaCa2-package-manager and represent its packages within the web app

Additionally Django project provides an API for Broker communication (represented by ``broker_api`` app).

Main advantage over other services is unification of users database, along with remaining efficient with database
resources usage.

More about BaCa2 Django app
'''''''''''''''''''''''''''

.. toctree::
    :maxdepth: 2

    ../apps/main/index
    ../apps/course/index
    ../apps/package/index
    ../apps/broker_api/index
    ../apps/util/index

BaCa2-broker
------------

.. image:: ../../_static/gh_icon.svg
    :target: https://github.com/BaCa2-project/BaCa2-broker

BaCa2-broker is web server enabling communication between BaCa2 web application and KOLEJKA task scheduling platform.