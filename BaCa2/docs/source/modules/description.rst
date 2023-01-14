Structure description
=====================

Apps
----

There are 3 django apps:

#.  ``main`` - main application, overwrites basic User model and generates permissions network
    for connection with course.
#.  ``package`` - connects database with files-stored packages.
#.  ``course`` - implements course interactions. Every course has own databases, dynamically created.

And one non-django app named ``baca2-broker`` which translates submits to be understood by
`KOLEJKA system <https://kolejka.matinf.uj.edu.pl/>`_.

