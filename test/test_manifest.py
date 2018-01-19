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
import os, time, glob
import shutil

import yamanifest.manifest as mf

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
    shutil.copytree(os.path.join('test','testfiles'),os.path.join('test','testfiles_copy'))
    make_random_binary_file(os.path.join('test','testfiles_copy','25mb.bin'),25*1024*1024)
    make_random_binary_file(os.path.join('test','testfiles_copy','100mb.bin'),100*1024*1024)
 
def teardown_module(module):
    if verbose: print ("teardown_module   module:%s" % module.__name__)
    shutil.rmtree(os.path.join('test','testfiles_copy'),ignore_errors=True)
    os.remove(os.path.join('test','testfiles','manifest.mf1'))

def test_manifest_read_write():

    mf1 = mf.Manifest('manifest.mf1')

    files = ['file1','file2']

    for filepath in files:
        mf1.add(os.path.join('test',filepath),['md5','sha1'])

    mf1.dump()

    mf2 = mf.Manifest('manifest.mf1')
        
    mf2.load()

    assert(mf1.equals(mf2) == True)

def test_has_hash():

    mf1 = mf.Manifest('manifest.mf1')
        
    mf1.load()

    for filepath in mf1:
        assert(mf1.get(filepath,'md5') is not None)
        assert(mf1.get(filepath,'sha1') is not None)

def test_manifest_netcdf():

    with cd(os.path.join('test','testfiles')):

        mf1 = mf.Manifest('manifest.mf1')

        for filepath in glob.glob('*.nc'):
            mf1.add(filepath,['nchash','md5','sha1'])

        mf1.dump()

    with cd(os.path.join('test','testfiles_copy')):

        mf2 = mf.Manifest('manifest.mf2')
        
        for filepath in glob.glob('*.nc'):
            mf2.add(filepath,['nchash','md5','sha1'])

        mf2.dump()

    # Unequal because they contain different fullpaths
    assert(mf1.equals(mf2) == False)
    # Equal when paths ignored
    assert(mf1.equals(mf2,paths=False) == True)

def test_manifest_netcdf_changed_time():

    with cd(os.path.join('test','testfiles_copy')):

        mf3 = mf.Manifest('manifest.mf3')

        for filepath in glob.glob('*.nc'):
            touch(filepath)
            mf3.add(filepath,['nchash','md5','sha1'])

        mf3.dump()

        mf2 = mf.Manifest('manifest.mf2')
        mf2.load()

        assert(not mf3.equals(mf2))

        for filepath in mf2:

            hashvals = {}

            mf2.check_file(filepath, hashvals=hashvals)
            print(filepath,hashvals)


def test_manifest_hash_with_binhash():

    with cd(os.path.join('test','testfiles_copy')):

        mf4 = mf.Manifest('manifest.mf4')

        for filepath in glob.glob('*.bin'):
            mf4.add(filepath,hashfn='binhash')

        mf4.dump()
        assert(mf4.check())

        mf5 = mf.Manifest('manifest.mf5')

        for filepath in glob.glob('*.bin'):
            touch(filepath)
            mf5.add(filepath,hashfn='binhash')

        hashvals = {}
        assert(not mf4.check())
        assert(not mf5.equals(mf4))

def test_manifest_find():

    with cd(os.path.join('test','testfiles')):

        mf1 = mf.Manifest('manifest.mf1')

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

        mf2 = mf.Manifest('manifest.mf2')

        for filepath in glob.glob('*.nc'):
            mf1.add(filepath,['nchash'])

        mf2.update(mf1)

        assert(mf2.equals(mf1))

    # Make same manifest but from the root directory, so have different file
    # paths
    mf3 = mf.Manifest('manifest.mf3')
    
    for filepath in glob.glob(os.path.join('test','testfiles','*.nc')):
        mf3.add(filepath,['nchash'])

    mf3.update(mf1)

    # Manifests should not be equal, their filepaths differ
    assert(not mf3.equals(mf1))

def test_manifest_with_mixed_file_types():

    with cd(os.path.join('test','testfiles_copy')):

        mf6 = mf.Manifest('manifest.mf6')

        for filepath in glob.glob('*.bin') + glob.glob('*.nc'):
            mf6.add(filepath,hashfn=['nchash','binhash'])

        mf6.dump()
        assert(mf6.check())

