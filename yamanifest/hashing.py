#!/usr/bin/env python

"""
Copyright 2017 ARC Centre of Excellence for Climate Systems Science

author: Aidan Heerdegen <aidan.heerdegen@anu.edu.au>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import absolute_import, print_function

import hashlib
import io
import os
import sys

length=io.DEFAULT_BUFFER_SIZE
one_hundred_megabytes = 104857600

# List of supported hashes and the ordering used to determine relative expense of
# calculation
supported_hashes = [
    'binhash', 'binhash-nomtime', 'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'
]

def _binhash(path, size, include_mtime):
    m = hashlib.new('md5')
    with io.open(path, mode="rb") as fd:
        # Size limited hashing, so prepend the filename, size and optionally modification time 
        hashstring = os.path.basename(path) + str(os.path.getsize(path))
        if include_mtime:
            hashstring +=str(os.path.getmtime(path))
        m.update(hashstring.encode())
        tot = 0
        for chunk in iter(lambda: fd.read(length), b''):
            tot += len(chunk)
            if tot >= size:
                rem = (size-tot)
                if rem <= 0:
                    break
                chunk = chunk[:rem]
            m.update(chunk)
    return m.hexdigest()

def _hashlib(path, hashfn):
    # from https://stackoverflow.com/a/40961519
    m = hashlib.new(hashfn)
    with io.open(path, mode="rb") as fd:
        for chunk in iter(lambda: fd.read(length), b''):
            m.update(chunk)
    return m.hexdigest()

def hash(path, hashfn, size=one_hundred_megabytes):
    """ A simple wrapper that inspects the hashing function and intercepts
    calls to nchash and binhash so they are processed in a special way.

    TODO: make plugins that allow this transparently
    """
    size = size or one_hundred_megabytes
    if hashfn not in supported_hashes:
        sys.stderr.write('\nUnsupported hash function {}, skipping {}\n'.format(hashfn, path))
    try:
        if hashfn == 'binhash-xxh':
            return _binhash(path, size, True, use_xxh=True)
        elif hashfn == 'binhash':
            return _binhash(path, size, True)
        elif hashfn == 'binhash-nomtime':
            return _binhash(path, size, False)
        else:
            return _hashlib(path, hashfn)
    except IOError as e:
        sys.stderr.write('{}\nCannot hash, skipping {}\n'.format(str(e),path))
        return None
        

