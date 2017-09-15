#!/usr/bin/env python
# vim: softtabstop=2 ts=2:

import bisect
import json
import itertools
import os
import re
import subprocess
import sys

from common import *

class Generator(object):
  def __init__(self, root_out_dir, src_root):
    self._root_out_dir = root_out_dir
    self._src_root = src_root
    include_dirs = gn_desc(root_out_dir, '//sdk:sdk_library', 'include_dirs')['include_dirs']
    # disallow garnet/public include path obliteration; use -I compile options for these instead
    # (include_dirs will include a '//' catch-all)
    include_dirs = filter(lambda dir: re.match('.*/garnet/public/', dir) == None, include_dirs)
    # regex pattern of include dirs sorted from longest to shortest
    self._include_dirs = '(?:' + '|'.join(sorted(include_dirs, None, len, True)) + ')(.*)'

  def path(self, gn_path):
    """Turn a gn path into a real path"""
    return os.path.normpath(self._src_root + gn_path)

  def include_path(self, gn_path):
    """Turn a gn path into its include-relative equivalent."""
    # TODO(rosswang): No need to handle files off the include path yet
    return re.match(self._include_dirs, gn_path).group(1)

  def generate(self, targets, blacklist):
    blacklist.sort()
    already_processed = set()
    while targets:
      target = targets.pop()
      library = normalize_target(target)

      if library in already_processed:
        continue

      already_processed.add(library)
      print(library)

      blk_entry = bisect.bisect(blacklist, library)
      if (blk_entry > 0 and library.startswith(blacklist[blk_entry - 1])):
        continue

      library_desc = gn_desc(self._root_out_dir, library)

      if 'sources' in library_desc:
        for file in library_desc['sources']:
          if (file.endswith('.h')):
            print("--> %s" % file)
            yield file

      targets += library_desc['deps']

if __name__ == '__main__':
  src_root = None
  if len(sys.argv) < 4:
    sys.stderr.write('%s <root_out_dir> <src_root> <output_dir> !exclude_prefix1 ... target1 ...\n' % sys.argv[0])
    sys.exit(1)

  _, root_out_dir, src_root, output_dir = sys.argv[:4]
  targets = []
  extra_headers = []
  blacklist = []
  for arg in sys.argv[4:]:
    if arg.startswith('!'):
      blacklist.append(arg[1:])
    elif arg.endswith('.h'):
      extra_headers.append(arg)
    else:
      targets.append(arg)

  generator = Generator(root_out_dir, src_root)

  for file in itertools.chain(generator.generate(targets, blacklist), extra_headers):
    source = generator.path(file)
    abs_target = os.path.join(output_dir, generator.include_path(file))
    subprocess.check_call(['mkdir', '-p', os.path.dirname(abs_target)])
    subprocess.check_call(['cp', source, abs_target])
