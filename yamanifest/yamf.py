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

    subparsers = parser.add_subparsers(dest='command', title='Subcommands',help='Valid subcommands')

    # Add sub command
    parser_add = subparsers.add_parser('add', help='Add filepaths to manifest')
    parser_add.add_argument('-n','--name', default='manifest.yaml', action='store', help='Manifest file name')
    parser_add.add_argument("-f","--force", help="Force overwrite of existing manifest", action='store_true')
    parser_add.add_argument("-s","--hashes", help="Use only these hashing functions", action='append')
    parser_add.add_argument("files", help="File paths to add to manifest", nargs='+')

    # Check sub command
    parser_check = subparsers.add_parser('check', help='Check manifest')
    parser_check.add_argument('-n','--name', default='manifest.yaml', action='store', help='Manifest file name')
    parser_check.add_argument("-s","--hashes", help="Use only these hashing functions", action='append')
    parser_check.add_argument("-a","--any", help="Return true if any of the hashes match (default is true if all match)", action='store_true')
    parser_check.add_argument("files", help="Check only these files", nargs='*')

    return parser.parse_args(args)

def main(args):
    """
    Main routine. Takes return value from parse.parse_args as input
    """
    mf1 = mf.Manifest(args.name)
    if args.command == 'add':
        if os.path.exists(args.name):
            # If manifest exists load existing hash data unless --force
            if not args.force:
                mf1.load()
        mf1.add(args.files,hashfn=args.hashes,force=args.force)
        mf1.dump()

    elif args.command == 'check':
        hashvals = {}
        try:
            mf1.load()
        except:
            sys.exit(1)

        if args.any:
            condition = any
        else:
            condition = all
        if mf1.check(hashfn=args.hashes,hashvals=hashvals,condition=condition):
            print("{} :: hashes are correct".format(args.name))
            return True
        else:
            print("{} :: hashes are incorrect".format(args.name))
            print(hashvals)
            for filepath in hashvals:
                for fn in hashvals[filepath]:
                    print("hashes do not match for {}: fn: {}\n  new {} file {}".format(filepath,fn,hashvals[filepath][fn],mf1.data[filepath]["hashes"][fn]))
            sys.exit(1)


def main_parse_args(args):
    """
    Call main with list of arguments. Callable from tests
    """
    # Must return so that check command return value is passed back to calling routine
    # otherwise py.test will fail
    return main(parse_args(args))

def main_argv():
    """
    Call main and pass command line arguments. This is required for setup.py entry_points
    """
    main_parse_args(sys.argv[1:])

if __name__ == "__main__":

    main_argv()
