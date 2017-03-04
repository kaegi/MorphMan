#!/usr/bin/python

import os
import sys

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, THIS_DIR)
import morph.cli

morph.cli.main()
