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
  def __init__(self, fuchsia_root):
    self._root = fuchsia_root
    self._libraries = set()
    # regex pattern of include dirs sorted from longest to shortest
    self._include_dirs = '(?:' + '|'.join(sorted(gn_desc(
        '//sdk:sdk_library', 'include_dirs')['include_dirs'], None, len, True)
        ) + ')(.*)'

  def path(self, gn_path):
    """Turn a gn path into a real path"""
    return os.path.normpath(self._root + gn_path)

  def include_path(self, gn_path):
    """Turn a gn path into its include-relative equivalent."""
    # TODO(rosswang): No need to handle files off the include path yet
    return re.match(self._include_dirs, gn_path).group(1)

  def generate(self, targets, blacklist):
    blacklist.sort()
    while targets:
      target = targets.pop()
      library = normalize_target(target)

      if library in self._libraries:
        continue

      self._libraries.add(library)

      blk_entry = bisect.bisect(blacklist, library)
      if (blk_entry > 0 and library.startswith(blacklist[blk_entry - 1])):
        continue

      library_desc = gn_desc(library)

      if 'sources' in library_desc:
        for file in library_desc['sources']:
          if (file.endswith('.h')):
            yield file

      targets += library_desc['deps']

if __name__ == '__main__':
  fuchsia_root = None
  if len(sys.argv) < 4:
    sys.stderr.write('%s <root> <output_dir> !exclude_prefix1 ... target1 ...\n' % sys.argv[0])
    sys.exit(1)

  _, root, output_dir = sys.argv[:3]
  targets = []
  extra_headers = []
  blacklist = []
  for arg in sys.argv[3:]:
    if arg.startswith('!'):
      blacklist.append(arg[1:])
    elif arg.endswith('.h'):
      extra_headers.append(arg)
    else:
      targets.append(arg)

  generator = Generator(root)

  for file in itertools.chain(generator.generate(targets, blacklist), extra_headers):
    source = generator.path(file)
    abs_target = os.path.join(output_dir, generator.include_path(file))
    subprocess.check_call(['mkdir', '-p', os.path.dirname(abs_target)])
    subprocess.check_call(['cp', source, abs_target])
