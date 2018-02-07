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
import sys, os, time, glob
import shutil
import pdb # Add pdb.set_trace() to set breakpoints

print("Version: {}".format(sys.version))

from yamanifest import manifest as mf
from yamanifest import yamf

verbose = True

import os
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

def setup_module(module):
    if verbose: print ("setup_module      module:%s" % module.__name__)
    if verbose: print ("Python version: {}".format(sys.version))
    shutil.copytree(os.path.join('test','testfiles'),os.path.join('test','testfiles_copy'))
    make_random_binary_file(os.path.join('test','testfiles_copy','25mb.bin'),25*1024*1024)
    make_random_binary_file(os.path.join('test','testfiles_copy','100mb.bin'),100*1024*1024)
 
def teardown_module(module):
    if verbose: print ("teardown_module   module:%s" % module.__name__)
    shutil.rmtree(os.path.join('test','testfiles_copy'),ignore_errors=True)
    os.remove(os.path.join('test','testfiles','mf1.yaml'))

def test_manifest_read_write():

    mf1 = mf.Manifest('mf1.yaml')

    files = ['file1','file2']

    for filepath in files:
        mf1.add(os.path.join('test',filepath),['md5','sha1'])

    assert(len(mf1) == len(files))

    mf1.dump()

    mf2 = mf.Manifest('mf1.yaml')
        
    mf2.load()

    assert(mf1.equals(mf2) == True)

    # Test chained load
    mf2 = mf.Manifest('mf1.yaml').load()

    assert(mf1.equals(mf2) == True)

def test_has_hash():

    mf1 = mf.Manifest('mf1.yaml')
        
    mf1.load()

    for filepath in mf1:
        assert(mf1.get(filepath,'md5') is not None)
        assert(mf1.get(filepath,'sha1') is not None)

def test_manifest_netcdf():

    with cd(os.path.join('test','testfiles')):

        mf1 = mf.Manifest('mf1.yaml')

        for filepath in glob.glob('*.nc'):
            mf1.add(filepath,['nchash','md5','sha1'])

        mf1.dump()

    with cd(os.path.join('test','testfiles_copy')):

        mf2 = mf.Manifest('mf2.yaml')
        
        for filepath in glob.glob('*.nc'):
            mf2.add(filepath,['nchash','md5','sha1'])

        mf2.dump()

    # Unequal because they contain different fullpaths
    assert(mf1.equals(mf2) == False)
    # Equal when paths ignored
    assert(mf1.equals(mf2,paths=False) == True)

def test_manifest_netcdf_changed_time():

    with cd(os.path.join('test','testfiles_copy')):

        mf3 = mf.Manifest('mf3.yaml')

        for filepath in glob.glob('*.nc'):
            touch(filepath)
            mf3.add(filepath,['nchash','md5','sha1'])

        mf3.dump()

        mf2 = mf.Manifest('mf2.yaml')
        mf2.load()

        assert(not mf3.equals(mf2))

        for filepath in mf2:

            hashvals = {}

            mf2.check_file(filepath, hashvals=hashvals)
            print(filepath,hashvals)


def test_manifest_hash_with_binhash():

    with cd(os.path.join('test','testfiles_copy')):

        mf4 = mf.Manifest('mf4.yaml')

        for filepath in glob.glob('*.bin'):
            mf4.add(filepath,hashfn='binhash')

        mf4.dump()
        assert(mf4.check())

        mf5 = mf.Manifest('mf5.yaml')

        for filepath in glob.glob('*.bin'):
            touch(filepath)
            mf5.add(filepath,hashfn='binhash')

        hashvals = {}
        assert(not mf4.check())
        assert(not mf5.equals(mf4))

def test_manifest_find():

    with cd(os.path.join('test','testfiles')):

        mf1 = mf.Manifest('mf1.yaml')

        mf1.load()

    for filepath in mf1:
        # Test for hashes we know should be in the manifest
        for hashfn in ['nchash','md5','sha1']:
            hashval = mf1.get(filepath,hashfn)
            print(hashfn,hashval,filepath,mf1.find(hashfn,hashval))
            assert(mf1.find(hashfn,hashval) == filepath)

        # Test for one we know shouldn't be there
        for hashfn in ['binhash',]:
            hashval = mf1.get(filepath,hashfn)
            print(hashfn,hashval,filepath,mf1.find(hashfn,hashval))
            assert(mf1.find(hashfn,hashval) == None)

    with cd(os.path.join('test','testfiles')):

        mf2 = mf.Manifest('mf2.yaml')

        for filepath in glob.glob('*.nc'):
            mf1.add(filepath,['nchash'])

        mf2.update(mf1)

        assert(mf2.equals(mf1))

    # Make same manifest but from the root directory, so have different file
    # paths
    mf3 = mf.Manifest('mf3.yaml')
    
    for filepath in glob.glob(os.path.join('test','testfiles','*.nc')):
        mf3.add(filepath,['nchash'])

    mf3.update(mf1)

    # Manifests should not be equal, their filepaths differ
    assert(not mf3.equals(mf1))

def test_manifest_with_mixed_file_types():

    with cd(os.path.join('test','testfiles_copy')):

        mf6 = mf.Manifest('mf6.yaml')

        for filepath in glob.glob('*.bin') + glob.glob('*.nc'):
            mf6.add(filepath,hashfn=['nchash','binhash'])

        mf6.dump()
        assert(mf6.check())

        # Should have no nchash for the bin files
        for filepath in glob.glob('*.bin'):
            assert(mf6.get(filepath,hashfn='nchash') == None)


def test_open_manifest_and_add():

    # Create manifest as above, but in two steps, writing out
    # the manifest file in between, deleting the object and reading
    # it back in and then adding the second lot of files
    with cd(os.path.join('test','testfiles_copy')):

        mf7 = mf.Manifest('mf7.yaml')

        for filepath in glob.glob('*.nc'):
            mf7.add(filepath,hashfn=['nchash','binhash'])

        mf7.dump()

        del(mf7)

        mf7 = mf.Manifest('mf7.yaml')
        mf7.load()

        for filepath in glob.glob('*.bin'):
            mf7.add(filepath,hashfn=['nchash','binhash'])

        mf7.dump()

        del(mf7)

        mf7 = mf.Manifest('mf7.yaml')
        mf7.load()
        mf6 = mf.Manifest('mf6.yaml')
        mf6.load()

        assert(mf7.equals(mf6))


def test_yamf():

    # Create manifest as above, but in two steps, writing out
    # the manifest file in between, deleting the object and reading
    # it back in and then adding the second lot of files
    with cd(os.path.join('test','testfiles_copy')):

        files  = glob.glob('*.bin') + glob.glob('*.nc')
        yamf.main_parse_args(["add","-n","mf8.yaml", "-s", "binhash", "-s", "nchash"] + files)

        mf8 = mf.Manifest('mf8.yaml')
        mf8.load()

        mf6 = mf.Manifest('mf6.yaml')
        mf6.load()

        assert(mf8.equals(mf6))
        assert(yamf.main_parse_args(["check","-n","mf8.yaml", "-s", "binhash", "-s", "nchash"]))


def test_shortcircuit_condition():

    with cd(os.path.join('test','testfiles_copy')):

        mf8 = mf.Manifest('mf8.yaml')
        mf8.load()
        assert(mf8.check())

        # Alter a hash and make sure check fails

        files  = glob.glob('*.bin') + glob.glob('*.nc')

        print(files[-1])
        print(mf8.data[files[-1]])

        mf8.data[files[-1]]["hashes"]["binhash"] = 0
        
        print(mf8.data[files[-1]])
        print(mf8.check())

        assert(not mf8.check())

        # Reload and check it reads in properly again

        mf8.load()
        assert(mf8.check())

        mf8.data[files[-1]]["hashes"]["binhash"] = 0

        # nchash should not be true. This behaviour has changed.
        # Decided an entry with no hash defined should be false to
        # trigger actions to create a new hash
        assert(not mf8.check(hashfn='nchash'))
        # binhash should not be true (set to incorrect value above)
        assert(not mf8.check(hashfn='binhash'))

        # Set truth condition to any, so happy if any of the hashes
        # are correct
        assert(mf8.check(condition=any))
        assert(yamf.main_parse_args(["check","-n","mf8.yaml","--any"]))

        # These options are essentially contradictory. shortcircuit
        # will in effect override the condition option. In this case
        # it returns true because the first hash it tested is true
        # Removed test as it is essentially non-deterministic about
        # which hash it encounters first. Was true for python3, false
        # for python27
        # assert(mf8.check(shortcircuit=True,condition=all))


def test_shortcircuit_add():

    with cd(os.path.join('test','testfiles_copy')):

        mf6 = mf.Manifest('mf6.yaml')

        for filepath in glob.glob('*.bin') + glob.glob('*.nc'):
            mf6.add(filepath,hashfn=['nchash','binhash'],shortcircuit=True)

        mf6.dump()
        assert(mf6.check())

        # Should have no nchash for the bin files
        for filepath in glob.glob('*.bin'):
            assert(mf6.get(filepath,hashfn='nchash') == None)

        # Should have no binhash for the netcdf files
        for filepath in glob.glob('*.nc'):
            assert(mf6.get(filepath,hashfn='binhash') == None)

        print(mf6.data)

def test_malformed_file():

    with cd(os.path.join('test','testfiles_copy')):

        mf9 = mf.Manifest('mf9.yaml')

        for filepath in glob.glob('*.nc'):
            mf9.add(filepath,['nchash','md5','sha1'])

        # Intentionally alter the format string
        mf9.header["format"] = 'bogus'
        mf9.dump()

        mf10 = mf.Manifest('mf9.yaml')
        with pytest.raises(ValueError) as e:   
            mf10.load()
        print(str(e.value))
        assert(str(e.value) == 'Not yamanifest format: bogus')
