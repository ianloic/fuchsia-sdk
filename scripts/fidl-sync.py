#!/usr/bin/env python

import sys

from common import *

for fidl in sys.argv[1:]:
    print fidl
    print normalize_target(fidl) + '_sync'
