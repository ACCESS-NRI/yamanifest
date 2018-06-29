#!/usr/bin/env python

"""
Copyright 2018 ARC Centre of Excellence for Climate Systems Science

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

import os, sys
import fnmatch
import functools
import itertools
import magic
import fs

try:
    from pathlib import Path
    Path().expanduser()
except (ImportError,AttributeError):
    from pathlib2 import Path

# https://stackoverflow.com/a/25413436
def find_files(dir_path=None, patterns=None):
    """
    Returns a generator yielding files matching the given patterns
    :type dir_path: str
    :type patterns: [str]
    :rtype : [str]
    :param dir_path: Directory to search for files/directories under. Defaults to current dir.
    :param patterns: Patterns of files to search for. Defaults to ["*"]. Example: ["*.json", "*.xml"]
    """
    path = dir_path or "."
    path_patterns = patterns or ["*"]

    for root_dir, dir_names, file_names in os.walk(path):
        filter_partial = functools.partial(fnmatch.filter, file_names)

        for file_name in itertools.chain(*map(filter_partial, path_patterns)):
            yield os.path.join(root_dir, file_name)

def get_protocol(fsobj):
    """
    Return the FS url protocol for a given FS object
    """
    if 'tarfs' in str(type(fsobj)):
        return 'tar'
    if 'zipfs' in str(type(fsobj)):
        return 'zip'

def get_fs_url(fsobj,localpath=None,full=False):
    """
    Format a python FS URL from information in an existing FS object.
    Optionally specify the full filesystem path rather than the relative 
    path. Use localpath if it is defined
    """
    path = fsobj._file
    if full:
        path = Path.cwd() / path
    url = "{protocol}://{path}".format(protocol=get_protocol(fsobj),path=path)
    if localpath is not None:
        url = url + '!' + localpath
    return url

def get_archive_urls(archivepath):
    """
    Open an archive file (tar/zip), find the contents and return them
    as fs urls
    """

    # Determine if it is already a URL, if not infer the filetype?
    fsobj = fs.open_fs(archivepath)

    paths = []
    fullpaths = []

    for path in fsobj.walk.files():
        paths.append(get_fs_url(fsobj,path))

    return paths

def is_archive(path):
    """
    Return True if the path is a an archive, zip or tar, or compressed tar
    """
    def fullmimetype(mimetype):
        return "application/{}".format(mimetype)

    tarfile = fullmimetype('x-tar')
    zipfile = fullmimetype('zip')

    mag = magic.Magic(mime=True,uncompress=False)                                                                                                                      
    if mag.from_file(path) in (tarfile, zipfile):
        return True
    mag = magic.Magic(uncompress=True,mime=True)                                                                                                                      
    if mag.from_file(path) in (tarfile,):
        return True 

    return False

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def make_random_binary_file(fname,size):
    numbytes = 1024 # replace 1024 with size_kb if not unreasonably large
    randombytes = os.urandom(numbytes)
    pos = 0
    print("Writing {}".format(fname))
    with open(fname, 'wb') as fout:
        while pos < size:
            fout.write(randombytes)
            pos += numbytes
        fout.truncate(size)

class cd:
    """Context manager for changing the current working directory
    https://stackoverflow.com/a/13197763"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
