#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run from command line
"""
import sys
import rigproc
from rigproc.central import main


def run(args=None):
    if args is None:
        args = sys.argv[1:]
    if args[0] == '-v' or args[0] == '--version':
        try:
            version= rigproc.__version__
        except:
            version= 'unknown'
        print(version)
        return version
    print("running! " + str(args))
    main.runrig(args[0])

if __name__ == "__main__":
    run()

