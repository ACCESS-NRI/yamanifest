=============================
yamanifest
=============================

General YAML manifest format

.. image:: https://readthedocs.org/projects/yamanifest/badge/?version=latest
  :target: https://readthedocs.org/projects/yamanifest/?badge=latest
.. image:: https://badge.fury.io/py/yamanifest.svg
  :target: https://pypi.python.org/pypi/yamanifest

.. content-marker-for-sphinx

Python package to generate YaML formatted manifests. This means multiple
checksums can be stored for each file, allowing cheap checksum operations
to cascade to more expensive hashes if required.


-------
Install
-------

Conda install::

    conda install -c access-nri yamanifest

Pip install (into a virtual environment)::

    pip install yamanifest

---
Use
---

See the `full usage documentation <https://yamanifest.readthedocs.io>`_ for comprehensive examples and API reference.

Quick example:

.. code-block:: bash

    yamf add -n manifest.yaml file1.txt file2.txt
    yamf check -n manifest.yaml

Or programmatically:

.. code-block:: python

    from yamanifest import Manifest
    
    manifest = Manifest('manifest.yaml')
    manifest.add(['file1.txt', 'file2.txt'])
    manifest.dump()
    
    # Later, verify files
    manifest = Manifest('manifest.yaml').load()
    if manifest.check():
        print("Files are valid")

---------

-------
Develop
-------

Development install::

    git checkout https://github.com/ACCESS-NRI/yamanifest
    cd yamanifest
    conda env create -f .conda/env_dev.yml
    source activate yamanifest-dev

Run tests::

    python -m pytest -s
