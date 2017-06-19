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

import os
import re
import subprocess
import sys
import yaml

from common import *

def is_dart_package(desc):
    return (desc['type'] == 'action' and
            desc['script'] == '//build/dart/gen_dot_packages.py')


class DartPackage(object):
    def __init__(self, target, desc):
        self.target = target
        self.desc = desc
        self.package_name = self.arg_value('--package-name')
        self.package_source = self.arg_value('--source-dir')
        self.target_dir = os.path.normpath(
            os.path.join(os.environ['FUCHSIA_DIR'], re.sub(r':.*', '', target)[
                2:]))
        if self.is_pub_package():
            pubspec = os.path.join(
                os.path.dirname(self.package_source), 'pubspec.yaml')
            self.version = yaml.safe_load(open(pubspec))['version']
        else:
            # use the date of the most recent change in git in the version
            timestamp = subprocess.check_output(['git', '-C', self.target_dir,
                                                 'show', 'HEAD', '--no-patch',
                                                 '--format=%at']).strip()
            self.version = '0.0.' + timestamp

    def arg_value(self, name):
        args = self.desc['args']
        return args[args.index(name) + 1]

    def is_pub_package(self):
        return self.package_source.endswith('/lib') and os.path.exists(
            os.path.join(os.path.dirname(self.package_source), 'pubspec.yaml'))

# TODO(ianloic): canonicalize target names?
root_out_dir = sys.argv[1]
targets = list(sys.argv[2:])
target_deps = {}

dart_packages = []

while len(targets):
    target = targets.pop()
    desc = gn_desc(root_out_dir, target)
    deps = frozenset(desc['deps'])
    target_deps[target] = deps
    targets.extend(dep for dep in deps
                   if dep not in targets and dep not in target_deps)
    if is_dart_package(desc):
        dart_packages.append(DartPackage(target, desc))

for dart_package in dart_packages:
    if dart_package.is_pub_package():
        continue
    out_dir = os.path.join(os.environ['FUCHSIA_BUILD_DIR'], 'sdk', 'dart-pkg',
                           dart_package.package_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    subprocess.check_output(
        ['rsync', '--archive', '--delete', '--include=*.dart', '--exclude=*',
         dart_package.package_source + '/', out_dir + '/lib/'])
    with open(os.path.join(out_dir, 'pubspec.yaml'), 'w') as pubspec:
        pubspec.write('name: %s\n' % dart_package.package_name)
        pubspec.write('version: %s\n' % dart_package.version)
        dep_packages = [
            dep_package for dep_package in dart_packages
            if dep_package.target in target_deps[dart_package.target]
        ]
        if dep_packages:
            pubspec.write('deps:\n')
            for dep_package in dep_packages:
                if dep_package.is_pub_package():
                    pubspec.write('  %s: %s\n' % (dep_package.package_name,
                                                  dep_package.version))
                    pass
                else:
                    pubspec.write('  %s:\n' % dep_package.package_name)
                    pubspec.write('    path: ../%s\n' %
                                  dep_package.package_name)
