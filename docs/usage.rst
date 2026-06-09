=====
Usage
=====

Overview
========

The **yamanifest** package provides utilities for creating and managing YAML-formatted file manifests with multiple checksums (hashes). This allows you to:

- Store multiple hash algorithms for each file in a single manifest
- Perform cheap checksum operations first (e.g., fast xxHash)
- Cascade to more expensive hashes only when needed
- Verify file integrity with flexible hash matching

Installation
============

Via Conda
---------

.. code-block:: bash

    conda install -c access-nri yamanifest

Via pip
-------

.. code-block:: bash

    pip install yamanifest

Quick Start
===========

Creating a Manifest
-------------------

The easiest way to create a manifest is using the command-line tool ``yamf``:

.. code-block:: bash

    yamf add -n manifest.yaml file1.txt file2.txt

This creates a ``manifest.yaml`` file with hashes for the specified files. By default, two hash algorithms are used: ``binhash`` and ``md5``.

You can specify custom hash algorithms:

.. code-block:: bash

    yamf add -n manifest.yaml -s binhash-xxh -s sha1 -s md5 file1.txt file2.txt

Checking a Manifest
-------------------

Verify that files match the hashes stored in your manifest:

.. code-block:: bash

    yamf check -n manifest.yaml

This checks all files in the manifest. If all hashes match, it outputs:

.. code-block:: bash

    manifest.yaml :: hashes are correct

You can also check specific files:

.. code-block:: bash

    yamf check -n manifest.yaml file1.txt

To pass the check if **any** hash matches (instead of requiring all hashes to match):

.. code-block:: bash

    yamf check -n manifest.yaml --any

Programmatic Usage
==================

Python API
----------

Import the Manifest class:

.. code-block:: python

    from yamanifest import Manifest

Creating a Manifest Programmatically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create a new manifest
    manifest = Manifest('manifest.yaml')
    
    # Add files with default hashes (binhash and md5)
    manifest.add(['file1.txt', 'file2.txt'])
    
    # Save to YAML file
    manifest.dump()

You can specify custom hash functions:

.. code-block:: python

    # Add files with specific hashes
    manifest.add('file1.txt', hashfn=['binhash-xxh', 'md5', 'sha1'])
    
    # Add to all existing files in manifest
    manifest.add(hashfn='sha256')
    
    # Force overwrite existing hashes
    manifest.add('file1.txt', hashfn='md5', force=True)

Loading an Existing Manifest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create and load a manifest in one step (method chaining)
    manifest = Manifest('manifest.yaml').load()
    
    # Or load separately
    manifest = Manifest('manifest.yaml')
    manifest.load()

Checking Files
~~~~~~~~~~~~~~

.. code-block:: python

    # Check all files with all hashes
    if manifest.check():
        print("All files are valid")
    
    # Check with specific hash functions
    if manifest.check(hashfn=['md5', 'sha1']):
        print("MD5 and SHA1 hashes are valid")
    
    # Capture detailed hash results
    hashvals = {}
    if manifest.check(hashvals=hashvals):
        print("Files are valid")
    print(hashvals)  # Contains computed hash values
    
    # Use 'any' condition (pass if any hash matches, default is all)
    if manifest.check(condition=any):
        print("At least one hash matched for each file")

Working with Individual Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Check if a file is in the manifest
    if manifest.contains('file1.txt'):
        print("file1.txt is in the manifest")
    
    # Get a specific hash value
    md5_hash = manifest.get('file1.txt', 'md5')
    if md5_hash:
        print(f"MD5: {md5_hash}")
    
    # Delete a file from manifest
    manifest.delete('file1.txt')
    
    # Iterate over all files in manifest
    for filepath in manifest:
        print(filepath)
    
    # Get manifest size
    print(f"Total files: {len(manifest)}")

Comparing Manifests
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    manifest1 = Manifest('manifest1.yaml').load()
    manifest2 = Manifest('manifest2.yaml').load()
    
    if manifest1.equals(manifest2):
        print("Manifests are identical")
    else:
        print("Manifests differ")

Supported Hash Algorithms
==========================

The following hash algorithms are supported:

- ``binhash`` - Change detection hash only. Not suitable for file verification across filesystems.
- ``binhash-xxh`` - xxHash version of binhash. 
- ``md5`` - `MD5 <https://en.wikipedia.org/wiki/MD5>`_ (default)
- ``sha1`` - `SHA-1 <https://en.wikipedia.org/wiki/SHA-1>`_
- ``sha256`` - `SHA-256 <SHA2>`_
- ``sha512`` - `SHA-512 <SHA2>`_

.. _SHA2: https://en.wikipedia.org/wiki/SHA-2

You can check available hashes programmatically:

.. code-block:: python

    from yamanifest import supported_hashes
    print(supported_hashes())

Direct Hash Computation
=======================

You can also use the hashing module directly:

.. code-block:: python

    from yamanifest import hash
    
    # Compute a hash for a file
    md5_value = hash('file1.txt', 'md5')
    xxh_value = hash('file2.txt', 'binhash-xxh')

Manifest YAML Format
====================

The manifest file is a YAML document with two sections:

**Header Section** (metadata):

.. code-block:: yaml

    format: yamanifest
    version: 1.0

**Data Section** (file entries):

.. code-block:: yaml

    file1.txt:
      fullpath: /absolute/path/to/file1.txt
      hashes:
        binhash: abc123...
        md5: d41d8cd98f00b204e9800998ecf8427e
    file2.txt:
      fullpath: /absolute/path/to/file2.txt
      hashes:
        binhash: xyz789...
        md5: 5d41402abc4b2a76b9719d911017c592

Example Workflow
================

Complete Example
----------------

.. code-block:: python

    from yamanifest import Manifest
    
    # Step 1: Create a manifest for data files
    manifest = Manifest('data_manifest.yaml')
    manifest.add(['data/file1.csv', 'data/file2.csv'], 
                 hashfn=['binhash-xxh', 'md5'])
    manifest.dump()
    
    # Step 2: Later, verify the data hasn't changed
    manifest = Manifest('data_manifest.yaml').load()
    if manifest.check():
        print("Data files are unchanged")
    else:
        print("Data has been modified!")
    
    # Step 3: Add stronger verification with SHA256
    manifest.add(hashfn='sha256')
    manifest.dump()
    
    # Step 4: Verify with strong hash
    if manifest.check(hashfn='sha256'):
        print("SHA256 hash verification passed")

Command-Line Example
--------------------

.. code-block:: bash

    # Initialize manifest for project files
    yamf add -n project.yaml -s binhash-xxh -s sha1 \
        src/main.py src/utils.py tests/test_main.py
    
    # Check files before deployment
    yamf check -n project.yaml
    
    # Verify specific files
    yamf check -n project.yaml src/main.py
    
    # Check with lenient matching (any hash OK)
    yamf check -n project.yaml --any

Advanced Features
=================

Method Chaining
---------------

Many methods support chaining:

.. code-block:: python

    manifest = Manifest('manifest.yaml').load()  # Returns self after load

Multiprocessing
---------------

The Manifest class automatically uses multiprocessing when computing hashes. It detects the number of CPU cores available and distributes work accordingly.

Custom File Paths
-----------------

When adding files to a manifest, you can specify custom fullpaths:

.. code-block:: python

    manifest.add(['relative/path.txt'], 
                 fullpaths=['/absolute/path/to/file.txt'])

Shortcircuit Hashing
--------------------

Use the ``shortcircuit`` parameter to stop after the first successful hash:

.. code-block:: python

    manifest.add('file.txt', 
                 hashfn=['binhash-xxh', 'md5'], 
                 shortcircuit=True)

Error Handling
==============

The package raises exceptions for common errors:

.. code-block:: python

    from yamanifest import Manifest, HashExists, FilePathNonexistent, HashNonexistent
    
    try:
        manifest = Manifest('manifest.yaml').load()
    except FileNotFoundError:
        print("Manifest file does not exist")
    except ValueError as e:
        print(f"Invalid manifest format: {e}")
    
    try:
        manifest.get('nonexistent.txt', 'md5')
    except FilePathNonexistent:
        print("File not in manifest")

Tips and Best Practices
=======================

1. **Use xxHash for Speed**: When speed is important, use ``binhash-xxh`` as your first hash:

   .. code-block:: bash

       yamf add -n manifest.yaml -s binhash-xxh -s md5 large_file.bin

2. **Cascade Hashes**: Store fast hashes for quick checks and slow hashes for thorough verification
3. **Multiple Algorithms**: Store multiple hashes to detect collisions and provide redundancy
4. **Version Control**: Commit manifest files to version control alongside your data
5. **Parallel Processing**: The library automatically uses all available CPU cores

For More Information
====================

- Repository: https://github.com/ACCESS-NRI/yamanifest
- PyPI Package: https://pypi.org/project/yamanifest/
