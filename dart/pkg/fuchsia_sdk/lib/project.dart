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

import 'dart:io';
import 'package:yaml/yaml.dart';
import 'package:path/path.dart' as path;

import "paths.dart";

class Project {
  // The packages map from pubspec.yaml
  YamlMap _packages;

  // The paths for the Fuchsia SDK referenced by this project.
  SdkPaths sdkPaths;

  Project([String directory]) {
    if (directory == null) {
      directory = Directory.current.path;
    }

    File pubspecLock = new File("pubspec.lock");
    YamlMap pubspecYaml = loadYaml(pubspecLock.readAsStringSync());
    _packages = pubspecYaml["packages"];
    sdkPaths = new SdkPaths(path.canonicalize(
        _packages["fuchsia_sdk"]["description"]["path"] + '/../../..'));
  }

  bool get flutter => _packages.containsKey("flutter");
}
