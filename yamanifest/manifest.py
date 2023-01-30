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

from six.moves import zip

import os
import sys
import yaml
import copy
import subprocess
import multiprocessing as mp
from collections import defaultdict

from .hashing import hash, supported_hashes
from yamanifest.utils import find_files

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

    def __init__(self, path, hashes=None, **kwargs):
        """
        Return a Manifest object, initialised with a path
        to the manifest file. Optionally specify default
        order of hashes to use when checking manifest validity
        """
        self.path = path
        self.data = {}
        self.header = {}
        try:
            self.numproc = mp.cpu_count()
        except NotImplementedError:
            self.numproc = 1
        for key, val in kwargs.items():
            setattr(self, key, val)
        self.iter = 0
        if hashes is None:
            self.hashes = set(['binhash','md5'])
        else:
            self.hashes = set(hashes)
        # self.lookup = {}
        # Meta data for the yamanifest file version. This is file type
        # version, not library version. Use update in case extra meta
        # data was defined in arguments
        self.header.update({ 'format':'yamanifest', 'version':1.0 })

            
    def __iter__(self):
        """
        Iterator method
        """
        for file in self.data:
            yield file

    def __len__(self):
        """
        Return the number of filepaths in the manifest object
        """
        return len(self.data)

    def load(self):
        """
        Load manifest from YAML file
        """
        try:
            with open(self.path, 'r') as file:
                self.header, self.data = yaml.safe_load_all(file)
            if "format" not in self.header:
                raise ValueError('Not yamanifest format')
            if self.header["format"] != 'yamanifest':
                raise ValueError('Not yamanifest format: {}'.format(self.header["format"]))
        except Exception as e:
            sys.stderr.write('Error parsing yamanifest file: {} :: {}\n'.format(self.path,str(e)))
            raise
            
        # self._make_lookup()

        # Allow chaining a load to creating a new instance
        return self
        
    def dump(self):
        """
        Dump manifest from YAML file
        """
        with open(self.path, 'w') as file:
            file.write(yaml.dump_all([self.header, self.data], default_flow_style=False))

    def delete(self, filepath):
        """
        Delete item for filepath in manifest
        """
        del(self.data[filepath])

    def add(self, filepaths=None, hashfn=None, force=False, shortcircuit=False, fullpaths=None):
        """
        Add hash value for filepath given a hashing function (hashfn).
        If no filepaths defined, default to all current filepaths, and in
        this way can add a hash to all existing filepaths.
        If there is already a hash value only overwrite if force=True,
        otherwise raise exception.
        """

        if filepaths is None:
            filepaths = self.data.keys()
        else:
            if type(filepaths) is str:
                filepaths = [filepaths,]

        if fullpaths is None:
            fullpaths = [None] * len(filepaths)
        else:
            if type(fullpaths) is str:
                fullpaths = [fullpaths,]
            assert(len(filepaths) == len(fullpaths))

        tmpfilepaths = []
        tmpfns = []

        results = defaultdict(dict)

        for (filepath,fullpath) in zip(filepaths,fullpaths):
            
            # These must be defined so that queries do not fail later
            if filepath not in self.data:
                self.data[filepath] = {}

            if 'hashes' not in self.data[filepath]:
                self.data[filepath]["hashes"] = {}

            if fullpath is None:
                self.data[filepath]['fullpath'] = os.path.realpath(filepath)
            else:
                self.data[filepath]['fullpath'] = fullpath

            if hashfn is None:
                fns = self.hashes
            else:
                if type(hashfn) is str:
                    fns = [hashfn,]
                else:
                    fns = hashfn
                # Need to add any hash function we use to the list of default hashes
                for fn in fns:
                    self.hashes.add(fn)

            for fn in fns:
                if fn in self.data[filepath]["hashes"] and not force:
                    # Don't try and add a hash if it already exists
                    continue
                tmpfilepaths.append(filepath)
                tmpfns.append(fn)
        
        results = self.calc_hashes(tmpfilepaths, tmpfns)
                
        for filepath in results:

            # Get dict of current hashes for filepath
            hashes = {}
            if "hashes" in self.data[filepath]:
                hashes = copy.deepcopy(self.data[filepath]["hashes"])
                
            fns = []
            if hashfn is None:
                fns = self.hashes
            else:
                if type(hashfn) is str:
                    fns = [hashfn,]
                else:
                    fns = hashfn

            for fn in fns:

                # if fn not in results[filepath]:
                #     continue

                hashval = results[filepath][fn]
                
                # If we've used an incompatible hashing function it will return
                # None and we will silently discard this hash, or if the filepath
                # is unhashable
                if hashval is not None:
                    if fn in hashes:
                        if hashes[fn] != hashval:
                            if not force:
                                continue
                            
                    # Set new value for this hash function
                    hashes[fn] = hashval

                    if shortcircuit:
                        break

            # Only save data to manifest if a hash was successfully generated or
            # there were existing hashes, else delete it
            if len(hashes) > 0:
                self.data[filepath]["hashes"] = hashes
            else:
                del(self.data[filepath])

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
                # Check we have a valid hash value (can't just be whitespace)
                if not hashval.strip():
                    hashval = False
                # else:
                #     print("hash value not defined {}".format(hashval))
            # else:
                # print("hash {} not in manifest".format(hashfn))
        # else:
            # print("{} not in manifest".format(filepath))

        return hashval
        
    def calc_hashes(self, filepaths, hashfns):
        """
        Calculate hash values for a number of filepaths and hash function combinations
        """
        
        # print("Spawning pool")
        pool = mp.Pool(processes=self.numproc) #,maxtasksperchild=50)

        results = defaultdict(dict)

        # print("Queuing jobs")
        for filepath, fn in zip(filepaths,hashfns):
            results[filepath][fn] = pool.apply_async(hash, args=(self.data[filepath]["fullpath"], fn))

        pool.close()
        pool.join()

        # print("Retrieving results")
        for filepath, fn in zip(filepaths,hashfns):
            # Get result of multiprocessing step. Be careful altering this
            # loop, as this is saving the result back to the dictionary
            results[filepath][fn] = results[filepath][fn].get()

        return results

    def check_file(self, filepaths, hashfn=None, hashvals=None, shortcircuit=False, condition=all):
        """
        Check hash value for a filepath given a hashing function (hashfn)
        matches stored hash value. Return values of non-matching hashes
        if hashvals dict supplied. If shortcircuit is True, will return True
        or False result with first True/False result
        """

        if type(filepaths) is str:
            filepaths = [ filepaths ]

        status = []

        if hashvals is not None:
            if type(hashvals) is dict:
                tmphashvals = defaultdict(dict)
            else:
                print("yamanifest :: manifest :: check_items :: hashvals must be a dict")
                raise
            
        results = defaultdict(dict)

        tmpfilepaths = []
        tmpfns = []

        for filepath in filepaths:

            fns = []

            if self.contains(filepath):
                hashes = self.data[filepath]["hashes"]
            else:
                raise FilePathNonexistent('{} does not exist in manifest'.format(filepath))
            
            if hashfn == None:
                if self.hashes is not None:
                    fns = self.hashes
                else:
                    fns = hashes.keys()
            elif type(hashfn) is str:
                fns = [hashfn,]
            else:
                fns = hashfn
                
            for fn in fns:
                # Ignore hash test if it does not exist in the manifest. Need this behaviour
                # so we can cascade hashes which in some cases are incompatible with certain
                # file types, e.g. nchash
                if fn in hashes:
                    tmpfilepaths.append(filepath)
                    tmpfns.append(fn)

        results = self.calc_hashes(tmpfilepaths, tmpfns)

        for filepath in filepaths:

            if filepath in results:
                filestatus = []

                for fn in results[filepath]:
                    if fn in self.data[filepath]["hashes"]:
                        # Get result of multiprocessing step
                        hashval = results[filepath][fn]
                        if hashval == self.data[filepath]["hashes"][fn]:
                            filestatus.append(True)
                            if shortcircuit:
                                break
                            else:
                                continue
                        else:
                            # Save these values if given list in which to return them
                            if hashvals is not None:
                                tmphashvals[filepath][fn] = hashval

                    # Should only get here if fn does not exist in manifest, or differs in value
                    filestatus.append(False)

                    if shortcircuit:
                        break

                # Only return True for a filepath if there was at least one
                # True hash. Ensures filepaths with no hash are False and must
                # be regenerated
                status.append(condition(filestatus) and len(filestatus)>0)
            else:
                # Fall here when hash specified but was not in manifest
                status.append(False)

        if hashvals is not None:
            hashvals.update(tmphashvals)

        return condition(status)

    def check(self, hashvals=None, **args):
        """
        Check hash value for all filepaths given a hashing function (hashfn)
        matches stored hash value
        """

        if hashvals is not None:
            if type(hashvals) is dict:
                hashvals.clear()
            else:
                print("yamanifest :: manifest :: check_items :: hashvals must be a dict")
                raise
            
        return self.check_file(filepaths=self.data.keys(),hashvals=hashvals,**args)

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

    def find(self, hashfn, hashval):
        """
        Find a hashfn value in a manifest. Return filepath on success, None otherwise
        """
        for filepath in self.data:
            if hashval == self.get(filepath, hashfn) and hashval is not None:
                return filepath

        return None

        
    def find_from_lookup(self, hashfn, hashval):
        """
        Find a hashfn value in a manifest. Return filepath on success, None otherwise
        """
        if (hashfn,hashval) in self.lookup:
            return self.lookup[(hashfn,hashval)]
        else:
            return None

    def _make_lookup(self):
        for filepath in self:
            for fn in self.data[filepath]["hashes"]:
                self._add_lookup(filepath,fn)

    def _add_lookup(self,filepath,hashfn):
        hashval = self.data[filepath]["hashes"][hashfn]
        self.lookup[(hashfn,hashval)] = filepath

    def update(self, other, newpath=None):
        """
        Add one manifest to another. Optionally replace path in fullpath with new path
        """
        mftmp = {}
        if newpath is not None:
            # Make a copy so we don't alter other
            mftmp = copy.deepcopy(other)
            # Cannot safely iterate over keys as the dict is being changed so iterate
            # over a precomputed list
            for filepath in list(other.data.keys()):
                mftmp.data[os.path.normpath(os.path.join(newpath,os.path.basename(filepath)))] = other.data[filepath]
                del mftmp.data[filepath]
        else:
            mftmp = other

        self.data.update(mftmp.data)

    def update_matching_hashes(self, other):
        """
        Update (add) hashes from other manifest where a match exists between a common
        hash
        """
        for filepath in self:
            for hashfn in self.data[filepath]["hashes"]:
                hashval = self.data[filepath]["hashes"][hashfn]
                newfilepath = other.find(hashfn,hashval)
                if newfilepath is not None:
                    # Check other hashes are consistent?
                    self.data[filepath]["hashes"].update(other.data[newfilepath]["hashes"])
                    break

    @classmethod
    def find_manifest(cls, dirpath):
        """
        Search a directory path and find first manifest file, return Manifest object else None 
        """
        for file in find_files(dirpath, ["*.yml","*.yaml"]):
            try:
                mftmp = cls(file) 
                mftmp.load()
            except:
                pass
            finally:
                if len(mftmp) > 0:
                    return mftmp

        return None
