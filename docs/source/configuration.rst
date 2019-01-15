Configuration
=============

.. toctree::
   :titlesonly:
   :maxdepth: 2

``degoss`` has a number of different configuration options which will be explained now.

``degoss_clean``
----------------

  Boolean. Default: ``true``.

If ``true``, ``degoss`` removes all temporary files after execution. If ``false``, the temporary directory is *not*
removed after execution.

``degoss_clean_on_failure``
---------------------------

  Boolean. Default: ``true``.

If ``true``, ``degoss`` will remove all temporary files after failure. If ``false``, when tests fail, the temporary
directory will *not* be removed.

``degoss_debug``
----------------

  Boolean. Default: ``false``.

If ``true``, set the logging level to ``DEBUG`` within the Python Ansible module. If ``false``, this level defaults
to ``INFO``.

For more information, see :doc:`logging <logging>`.

``goss_variables``
------------------

  Dictionary. Default ``{}``.

Additional variables to send to Goss during execution. All Ansible facts are exposed automatically to Goss at runtime,
but this can be used to send additional variables into the test execution context.

``goss_version``
----------------

  String. Default ``latest``.

The version of Goss to use. By default, this is set to the special value ``latest``, which will use the latest available
release of Goss from GitHub. Otherwise, pass a version like ``0.3.6`` to target a specific Goss release.

``goss_file``
-------------

  String. Default ``null``.

A path to the main Goss entrypoint YAML file to run tests with.

This path is resolved relative to the playbook's directory.

``goss_addtl_files``
--------------------

  List of Strings. Default ``[]``.

A list of additional Goss YAML files to copy to the test machine.

These paths are resolved relative to the playbook's directory.

``goss_addtl_dirs``
-------------------

  List of Strings. Default ``[]``.

A list of directories to copy to the test machine containing additional Goss YAML files.

These paths are resolved relative to the playbook's directory.
