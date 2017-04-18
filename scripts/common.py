#!/usr/bin/env python

import json
import os
import subprocess

def normalize_target(target):
    if ':' in target: return target
    return target + ':' + os.path.basename(target)

def gn_desc(target, *what_to_show):
    # gn desc may fail transiently for an unknown reason; retry loop
    for i in xrange(2):
        desc = subprocess.check_output([
            os.path.join(os.environ['FUCHSIA_DIR'], 'packages', 'gn',
                         'desc.py'), '--format=json', target
        ] + list(what_to_show))
        try:
            output = json.loads(desc)
            break
        except ValueError:
            if i >= 1:
                print 'Failed to describe target ', target, '; output: ', desc
                raise

    if target not in output:
        target = normalize_target(target)
    return output[target]
