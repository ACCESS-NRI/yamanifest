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
import os
import sys
from nchash import NCDataHash, NotNetcdfFileError
import fs
from fs import path as fspath

length=io.DEFAULT_BUFFER_SIZE
one_hundred_megabytes = 104857600

# List of supported hashes and the ordering used to determine relative expense of
# calculation
supported_hashes = ['nchash', 'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']

def hash(path, hashfn, size=one_hundred_megabytes, verbose=False):
    """ A simple wrapper that inspects the hashing function and intercepts
    calls to nchash and binhash so they are processed in a special way.

    TODO: make plugins that allow this transparently
    """

    try:
        presult = None; fsobj = None; lpath = None
        # Determine if path is a fs url or ordinary path, and
        # open a fs object and set lpath accordingly
        try:
            presult = fs.opener.parse(path)
        except fs.opener.errors.ParseError as e:
            if verbose: print("{} is not a fs2 URL".format(path))
        if presult is not None and presult.path is not None:
            fsobj, lpath = fs.opener.open(path,writeable=False)    
        else:
            # Is a normal path
            dirpath, lpath = fspath.split(path)
            fsobj = fs.open_fs(dirpath)

        if hashfn == 'nchash':
            hashval = ''
            m = NCDataHash(path)
            try:
                hashval = m.gethash()
            except NotNetcdfFileError as e:
                sys.stderr.write(str(e))
                hashval = None
            return hashval
        elif hashfn == 'binhash':
            m = hashlib.new('md5')
            info = fsobj.getdetails(lpath)
            with fsobj.openbin(lpath) as fd:
                # Size limited hashing, so prepend the filename, size and modification time 
                hashstring = fs.path.basename(path) + str(info.size) + info.modified.strftime("%s")
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
        else:
            # from https://stackoverflow.com/a/40961519
            m = hashlib.new(hashfn)
            with fsobj.openbin(lpath) as fd:
                for chunk in iter(lambda: fd.read(length), b''):
                    m.update(chunk)
            return m.hexdigest()

    except IOError as e:
        sys.stderr.write('{}\nCannot hash, skipping {}\n'.format(str(e),path))
        return None
        

