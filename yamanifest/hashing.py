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

from __future__ import print_function, absolute_import

import hashlib
import io
from nchash.nchash import NCDataHash

length=io.DEFAULT_BUFFER_SIZE

# List of supported hashes and the ordering used to determine relative expense of
# calculation
supported_hashes = ['nchash', 'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']

def hash(path, hashfn):
    """ A simple wrapper that inspects the hashing function and intercepts
    calls to nchash so they are processed in a special way.

    TODO: make plugins that allow this transparently
    """

    if hashfn == 'nchash':
        m = NCDataHash(path)
        return m.gethash()
    else:
        # from https://stackoverflow.com/a/40961519
        m = hashlib.new(hashfn)
        with io.open(path, mode="rb") as fd:
            for chunk in iter(lambda: fd.read(length), b''):
                m.update(chunk)
        return m.hexdigest()

