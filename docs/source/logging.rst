Logging
=======

.. toctree::
  :maxdepth: 2

``degoss`` uses regular Python logging to emit and capture logs generated during module execution. These logs can be
helpful in debugging test execution errors. Logs are stored temporarily in memory as well as to a temporary log file
on disk. If the Goss temporary root is ``/tmp/degoss.deadbeef``, logs will be written to
``/tmp/degoss.deadbeef/logs/degoss.log``.

A helpful configuration option is to set ``degoss_clean_on_failure`` to ``false``. When test failures occur,
temporary directories won't be cleaned up automatically, making it possible to poke around, read logs, and try to
troubleshoot the issue.

Setting the ``degoss_debug`` configuration option to ``true`` will configure logging to emit up to ``DEBUG`` level logs,
as opposed to ``INFO``, which is the default, yielding more information captured in the logs.

Goss execution errors, as opposed to Goss test failures, will emit the logging output to Ansible's output, which should
obviate the need for more extensive debugging.
