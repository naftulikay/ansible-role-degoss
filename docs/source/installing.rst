Installing Degoss
=================

.. toctree::
  :maxdepth: 2

Installing Degoss is fairly simple, as it is hosted on `Ansible Galaxy <https://galaxy.ansible.com/>`_ as
`naftulikay.degoss <https://galaxy.ansible.com/naftulikay/degoss>`_.

The role can be installed directly using the ``ansible-galaxy`` CLI:

.. code-block:: shell

  ansible-galaxy install naftulikay.degoss

Alternatively, you can add the role into a Galaxy requirements file like ``requirements.yml``:

.. code-block:: yaml
   :caption: **requirements.yml**

   ---
   - src: naftulikay.degoss

And then subsequently install it with the ``ansible-galaxy`` CLI:

.. code-block:: shell

  ansible-galaxy install --force --path .ansible/galaxy-roles -r requirements.yml

This will install the role into ``.ansible/galaxy-roles``. Make sure that this directory is on your Ansible roles
path:

.. code-block:: ini
   :caption: **ansible.cfg**

   [defaults]
   roles_path = .ansible/galaxy-roles

Now that we've installed the role, let's start using it.
