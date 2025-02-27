=============================
yamanifest
=============================

General YAML manifest format

.. image:: https://readthedocs.org/projects/yamanifest/badge/?version=latest
  :target: https://readthedocs.org/projects/yamanifest/?badge=latest
.. image:: https://travis-ci.org/aidanheerdegen/yamanifest.svg?branch=master
  :target: https://travis-ci.org/aidanheerdegen/yamanifest
.. image:: https://circleci.com/gh/coecms/yamanifest.svg?style=shield
  :target: https://circleci.com/gh/coecms/yamanifest
.. image:: http://codecov.io/github/aidanheerdegen/yamanifest/coverage.svg?branch=master
  :target: http://codecov.io/github/aidanheerdegen/yamanifest?branch=master
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

Build documentation::

    python setup.py build_sphinx
    firefox docs/_build/index.html

Upload documentation::

    git subtree push --prefix docs/_build/html/ origin gh-pages
