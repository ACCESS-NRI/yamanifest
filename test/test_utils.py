
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

from __future__ import print_function

import pytest
import sys
import shutil
import pdb # Add pdb.set_trace() to set breakpoints
import fs
from fs import copy, tarfs, zipfs
import magic

print("Version: {}".format(sys.version))

from yamanifest import utils

verbose = True

import os

archive_name = 'tmp_test'
types = {'tar' : 'tar', 'tar.gz' : 'tar', 'zip' : 'zip'}
files = {}

def setup_module(module):
    teardown_module(module)
    if verbose: print ("setup_module      module:%s" % module.__name__)
    if verbose: print ("Python version: {}".format(sys.version))

    for t, p in types.items():
        files[t] = '{}.{}'.format(archive_name,t)
        copy.copy_fs('test/archivedir', '{}://{}'.format(p,files[t]))
 
def teardown_module(module):
    if verbose: print ("teardown_module   module:%s" % module.__name__)
    # for f in files.values():
    #     os.remove(f)

def test_is_archive():
    for t, f in files.items():
        assert(utils.is_archive(f))

    assert(not utils.is_archive('test/file1'))

def test_get_protocol():
    for t, p in types.items():
        fsobj = fs.open_fs('{}://{}'.format(p,files[t]))
        assert(utils.get_protocol(fsobj) == types[t])
 
def test_make_fs_url():
    for t, f in files.items():
        fsobj = fs.open_fs('{}://{}'.format(types[t],files[t]))
        url = utils.get_fs_url(fsobj)
        # slightly silly test, just make sure we get back the url
        # used to open this file
        assert(url == '{}://{}'.format(types[t],files[t]))
        # generate the url for a file within the archive
        fsobj1, lpath = fs.opener.open(utils.get_fs_url(fsobj,'file1'),writeable=False)
        assert(lpath == 'file1')
        print(t,f,lpath,type(lpath))
        pdb.set_trace() 
        print(type(fsobj1.gettext(lpath)))
        assert(fsobj1.gettext(lpath) == 'alllal\n')
        # generate again using full path to archive file
        fsobj2, lpath = fs.opener.open(utils.get_fs_url(fsobj,'file1',full=True),writeable=False)
        assert(lpath == 'file1')
        assert(fsobj2.gettext(lpath) == 'alllal\n')

def test_get_archive_urls():

    for t, f in files.items():
        fsobj = fs.open_fs('{}://{}'.format(types[t],files[t]))
        assert(len(utils.get_archive_urls(fsobj)) == 3)

