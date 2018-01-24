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
import argparse
import yaml
from yamanifest import manifest as mf

def parse_args(args):
    """
    Parse arguments given as list (args)
    """
    parser = argparse.ArgumentParser(description="Run yamf on one or more files")
    parser.add_argument("-n","--name", help="Manifest file name", default='manifest.yaml')
    parser.add_argument("-f","--force", help="Force overwrite of existing manifest", action='store_true')
    parser.add_argument("-c","--check", help="Check manifest file hashes", action='store_true')
    parser.add_argument("-s","--hashes", help="Use only these hashing functions", action='append')
    parser.add_argument("inputs", help="files", nargs='*')

    return parser.parse_args(args)

def main(args):
    """
    Main routine. Takes return value from parse.parse_args as input
    """
    mf1 = mf.Manifest(args.name)

    if os.path.exists(args.name):
        # If manifest exists load existing hash data unless --force
        if not args.force:
            mf1.load()

    if args.check:
        if len(args.inputs) > 0:
            print("File arguments ignored with --check option", file=sys.stderr)
        hashvals = {}
        if mf1.check(hashfn=args.hashes,hashvals=hashvals):
            print("{} :: hashes are correct".format(args.name))
        else:
            print("{} :: hashes do not match! {}".format(args.name,hashvals))
            sys.exit(1)
    else:
        for filepath in args.inputs:
            mf1.add(filepath,hashfn=args.hashes,force=args.force)
        mf1.dump()
            

def main_parse_args(args):
    """
    Call main with list of arguments. Callable from tests
    """
    main(parse_args(args))

def main_argv():
    """
    Call main and pass command line arguments. This is required for setup.py entry_points
    """
    main_parse_args(sys.argv[1:])

if __name__ == "__main__":

    main_argv()
