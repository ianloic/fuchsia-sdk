#!/usr/bin/env python
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import glob
import json
import os
import subprocess
import sys

from common import *

class Generator(object):
  def __init__(self, fuchsia_root):
    self._root = fuchsia_root

  def _tweak_flags(self, flags):
    """Adjust CC/CXX/LD flags for out-of-tree use"""
    tweaked = []
    for flag in flags:
      if '=../' in flag:
        # an out-dir relative path
        flag = flag.replace('=../', '=' + self._root + '/out/')
      tweaked.append(flag)
    return tweaked

  def _path(self, gn_path):
    """Turn a gn path into a real path"""
    return os.path.normpath(self._root + gn_path)

  def _join(self, args):
    """Join a list of arguments to be passed to a shell"""
    return ' '.join(args)

  def generate(self, target):
    library_desc = gn_desc(target)

    # Start with the common cflags
    base_cflags = self._tweak_flags(library_desc['cflags'])
    # Add the include paths
    base_cflags += ['-I' + self._path(p) for p in library_desc['include_dirs']]
    base_cflags += ['-D' + d for d in library_desc['defines']]

    # Calculate the CC flags
    cflags = base_cflags + self._tweak_flags(library_desc['cflags_c'])

    # Calculate the CXX flags
    cxxflags = base_cflags + self._tweak_flags(library_desc['cflags_cc'])

    # Calculate the LD flags
    # TODO: don't hardcode -lmxio
    ldflags = self._tweak_flags(library_desc[
        'ldflags']) + ['-l' + l for l in library_desc['libs']] + [ '-lmxio' ]

    # Calculate the path to the library
    libs = [self._path(l) for l in library_desc['outputs']]

    # TODO: work out how to extract CC, CXX, LD from gn or ninja.
    toolchain_dir = glob.glob(self._root +
                              '/buildtools/toolchain/clang+llvm-*/bin/')
    assert (len(toolchain_dir) == 1)
    toolchain_dir = os.path.normpath(toolchain_dir[0])

    return {
        'CC': os.path.join(toolchain_dir, 'clang'),
        'CXX': os.path.join(toolchain_dir, 'clang++'),
        'LD': os.path.join(toolchain_dir, 'clang++'),
        'CFLAGS': self._join(cflags),
        'CXXFLAGS': self._join(cxxflags),
        'LDFLAGS': self._join(ldflags),
        'LIBS': self._join(libs),
    }


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--format', choices=('make', 'sh'), default='make')
  parser.add_argument('root')
  parser.add_argument('target')
  parser.add_argument('output')
  args = parser.parse_args()

  generator = Generator(args.root)

  with open(args.output, 'w') as f:
    for k, v in generator.generate(args.target).items():
      if args.format == 'make':
        f.write('%s=%s\n' % (k, v))
      else:
        f.write('%s="%s"\n' % (k, v))
