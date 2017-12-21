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
 
def teardown_module(module):
    if verbose: print ("teardown_module   module:%s" % module.__name__)
    shutil.rmtree(os.path.join('test','testfiles_copy'),ignore_errors=True)
    os.remove(os.path.join('test','testfiles','manifest.mf1'))

def test_manifest_read_write():

    mf1 = mf.Manifest('manifest.mf1')

    files = ['file1','file2']

    for file in files:
        mf1.add_item(os.path.join('test',file),['md5','sha1'])

    mf1.dump()

    mf2 = mf.Manifest('manifest.mf1')
        
    mf2.load()

    assert(mf1.equals(mf2) == True)

def test_manifest_netcdf():

    with cd(os.path.join('test','testfiles')):

        mf1 = mf.Manifest('manifest.mf1')

        for file in glob.glob('*.nc'):
            mf1.add_item(file,['nchash','md5','sha1'])

        mf1.dump()

    with cd(os.path.join('test','testfiles_copy')):

        mf2 = mf.Manifest('manifest.mf2')
        
        for file in glob.glob('*.nc'):
            mf2.add_item(file,['nchash','md5','sha1'])

        mf2.dump()

    # Unequal because they contain different fullpaths
    assert(mf1.equals(mf2) == False)
    # Equal when paths ignored
    assert(mf1.equals(mf2,paths=False) == True)

def test_manifest_netcdf_changed_time():

    with cd(os.path.join('test','testfiles_copy')):

        mf3 = mf.Manifest('manifest.mf3')

        for file in glob.glob('*.nc'):
            touch(file)
            mf3.add_item(file,['nchash','md5','sha1'])

        mf3.dump()

        mf2 = mf.Manifest('manifest.mf2')
        mf2.load()

        assert(mf3.equals(mf2) == False)
