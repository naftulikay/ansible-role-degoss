Using Degoss
============

.. toctree::
   :maxdepth: 2


Before jumping right into usage, let's describe what ``degoss`` actually *does* at runtime.

Workflow
--------

The ``degoss`` Ansible role essentially does the following:

 #. Create a temporary directory.
 #. Upload your Goss test files into this temporary directory.
 #. Download either the latest or a specific version of Goss.
 #. Execute the Goss tests, passing in Ansible facts and your own custom variables to Goss over standard input.
 #. Remove all traces of the test run by deleting the temporary directory.
 #. Report test results to Ansible's output.
 #. If tests failed, mark the task as failed.

A few notes on this architecture:

 - A design goal of ``degoss`` is to leave as few traces as possible on the host system, which is why it creates and
   subsequently *removes* a temporary directory during execution.
 - Security is also considered, with Ansible facts and custom user-defined variables being passed into the Goss process
   over standard input, rather than writing these to disk as files.

Basic Example
-------------

Let's start with a pretty basic example which uses a single Goss file.

Creating a Playbook
^^^^^^^^^^^^^^^^^^^

First, let's create our playbook:

.. code-block:: yaml
  :caption: **playbook.yml**

  ---
  - name: build
    hosts: all
    become: true
    tasks:
      - name: create directory
        file: path=/opt/new state=directory

  - name: test
    hosts: all
    roles:
      - role: naftulikay.degoss
        goss_file: goss.yml

This playbook contains two plays:

 - ``build`` which 'configures' each host
 - ``test`` which executes Goss tests against each host

We pass a single file, ``goss.yml`` to ``degoss``, which will use this file as the entrypoint for running Goss tests.

Creating a Goss Test File
^^^^^^^^^^^^^^^^^^^^^^^^^

Let's setup a simple Goss file for testing our build:

.. code-block:: yaml
  :caption: **goss.yml**

  ---
  file:
    '/opt/new':
      exists: true
      filetype: directory

This defines two tests:

 - that ``/opt/new`` exists
 - that ``/opt/new`` is a directory

`Please check out the official Goss docs <https://github.com/aelsabbahy/goss/blob/master/docs/manual.md>`_ for a
description of the tests available to Goss.

  **NOTE:** Goss-related files and directories are resolved *relative to the playbook's directory*. This example
  assumes that ``playbook.yml`` and ``goss.yml`` live in the same directory adjacent to each other.

Executing the Playbook and Tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's run our test::

   ansible-playbook playbook.yml

In the output, we can see that Goss has ran our test and no failures were encountered:

.. code-block:: plain

 TASK [naftulikay.degoss : run tests] *****************************************************
 ok: [sardaukar]

 Goss Tests Passed

 (Count: 2, Failed: 0, Skipped: 0)

This was too easy. Let's make it fail.

Test Failures
^^^^^^^^^^^^^

First, emend ``goss.yml`` to make some tests fail:

.. code-block:: yaml
  :caption: **goss.yml**

  ---
  file:
    '/opt/new':
      exists: false

This test should fail, as the directory exists. Let's run our playbook again and see what happens:


.. code-block:: plain

 TASK [naftulikay.degoss : run tests] *****************************************************
 fatal: [sardaukar]: FAILED! => {...}

 Goss Tests Failed

 File: /opt/new: exists:
 Expected
     <bool>: true
 to equal
     <bool>: false

Awesome! Now we can test our roles and playbooks using ``degoss`` even in continuous integration!
