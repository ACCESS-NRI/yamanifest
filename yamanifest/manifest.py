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

import os
import yaml
from .hashing import hash, supported_hashes

class HashExists(Exception):
    """Trying to add a hashed value when one already exists"""

class FilePathNonexistent(Exception):
    """Trying to check a hashed value when there is none"""

class HashNonexistent(Exception):
    """Trying to check a hashed value when there is none"""

class Manifest(object):
    """A manifest object

    Attributes:
        path: a Path object for the manifest file
        data: an dictionary of manifest items
    """

    def __init__(self, path, **kwargs):
        """
        Return a Manifest object
        """
        self.path = path
        self.data = { }
        for key, val in kwargs.items():
            setattr(self, key, val)
        self.iter = 0
        
            
    def __iter__(self):
        """
        Iterator method
        """
        for file in self.data:
            yield file

    def load(self):
        """
        Load manifest from YAML file
        """
        with open(self.path, 'r') as file:
            self.data = yaml.load(file)

    def dump(self):
        """
        Dump manifest from YAML file
        """
        with open(self.path, 'w') as file:
            file.write(yaml.dump(self.data, default_flow_style=False))

    def delete(self, filepath):
        """
        Delete item for filepath in manifest
        """
        del(self.data[filepath])

    def add(self, filepath, hashfn, force=False):
        """
        Add hash value for a filepath given a hashing function (hashfn).
        If there is already a hash value only overwrite if force=True,
        otherwise raise exception.
        """

        if filepath in self.data:
            hashes = self.data[filepath]["hashes"]
        else:
            self.data[filepath] = {}
            self.data[filepath]["hashes"] = {}
            hashes = self.data[filepath]["hashes"]

        # Save the latest full system path 
        self.data[filepath]['fullpath'] = os.path.realpath(filepath)

        if type(hashfn) is str:
            fns = [hashfn,]
        else:
            fns = hashfn
            
        for fn in fns:
            hashval = hash(filepath, fn)
            if fn in hashes:
                if hashes[fn] != hashval:
                    if not force:
                        raise HashExists('Tried to add {} to {}'.format(fn,filepath))

            # Set new value for this has function
            hashes[fn] = hashval

    def contains(self, filepath):
        """
        Return True if filepath is in manifest
        """

        return filepath in self.data

    def get(self, filepath, hashfn):
        """
        Return hash value for filepath and hash function. Return None if not defined
        """

        hashval = None
        if self.contains(filepath):
            if hashfn in self.data[filepath]["hashes"]:
                hashval = self.data[filepath]["hashes"][hashfn]
                # Check we have a value
                if hashval is not None and hashval.strip():
                    has_hash = True
                else:
                    print("hash value not defined {}".format(hashval))
            else:
                print("hash {} not in manifest".format(hashfn))
        else:
            print("{} not in manifest".format(filepath))

        return hashval
        
    def check_file(self, filepath, hashfns=None, hashvals=None):
        """
        Check hash value for a filepath given a hashing function (hashfn)
        matches stored hash value
        """

        fns = []

        if self.contains(filepath):
            hashes = self.data[filepath]["hashes"]
        else:
            raise FilePathNonexistent('{} does not exist in manifest'.format(filepath))

        if hashfns == None:
            fns = hashes.keys()
        elif type(hashfns) is str:
            fns = [hasfns,]
        else:
            fns = hashfns

        if hashvals is not None:
            if type(hashvals) is dict:
                hashvals.clear()
            else:
                print("yamanifest :: manifest :: check_items :: hashvals must be a dict")
                raise
            
        for fn in fns:
            hashval = hash(filepath, fn)
            # Save these values if given list in which to return them
            hashvals[fn] = hashval
            if fn not in hashes:
                hashvals[fn] = None
                return False
            if hashval != hashes[fn]:
                # Short circuit and return false.
                return False

        return True

    def fullpath(self, filepath):
        """
        Return fullpath string for filepath. None if not defined
        """

        if self.contains(filepath):
            return self.data[filepath]['fullpath']
        else:
            return None
        
    def equals(self, other, paths=True):
        """
        Test if this manifest is the same as another manifest object.
        Made this a bound method instead of overriding __eq__ as need to 
        qualify if equality also includes file paths
        """
        if isinstance(self, other.__class__):

            for file in self:
                if file not in other.data:
                    return False
                if paths:
                    if self.data[file]['fullpath'] != other.data[file]['fullpath']:
                        return False
                for fn, val in self.data[file]["hashes"].items():
                    if fn not in other.data[file]["hashes"]:
                        return False
                    if other.data[file]["hashes"][fn] != val:
                        return False

            return True

        else:
            return NotImplemented
