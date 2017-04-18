// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import 'dart:async';
import 'dart:io';

import 'package:args/args.dart';
import 'package:args/command_runner.dart';
import 'package:logging/logging.dart' show Logger;
import 'package:path/path.dart';

import '../../lib/paths.dart';
import '../../lib/project.dart';
import '../../lib/runprocess.dart';

class GenCommand extends Command {
  final String name = 'gen';
  final String description = 'Generate FIDL bindings';
  final Logger log = new Logger('gen');

  Project _project;

  Future run() async {
    _project = new Project();

    final Directory fidl_dir = new Directory('fidl');
    // TODO(ianloic): handle "fidl/" existing but not being a directory.
    if (!await fidl_dir.exists()) {
      log.info('${fidl_dir.absolute} does not exist.');
      return;
    }

    // TODO(ianloic): remove the gen/ directory

    List<String> fidls = [];
    await for (FileSystemEntity item in fidl_dir.list(recursive: true)) {
      if (item is File) {
        fidls.add(item.absolute.path);
      }
    }

    List<String> args = [
      'gen',
      // TODO(ianloic): add include paths for SDK FIDLs.
      '--output-dir', 'gen/',
      '--generators', '${_project.sdkPaths.targetOut}/legacy_generators/run_code_generators.py',
      '--src-root-path', fidl_dir.absolute.path,
      ];
    args.addAll(fidls);
    await runProcess('${_project.sdkPaths.targetOut}/fidl', args);

    // TODO(ianloic): Only generate Dart / remove non-Dart files.

    return;
  }
}


