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

import 'package:barback/barback.dart';
import 'package:yaml/yaml.dart';
import 'package:path/path.dart' as path;

import 'paths.dart';
import 'project.dart';
import 'runprocess.dart';

class FuchsiaTransformer extends AggregateTransformer {
  SdkPaths paths;
  bool flutter = false;

  FuchsiaTransformer.asPlugin(BarbackSettings settings) {
    Project project = new Project();
    paths = project.sdkPaths;
    flutter = project.flutter;
  }

  dynamic classifyPrimary(AssetId id) {
    return 'foo';
  }

  Future apply(AggregateTransform transform) async {
    List<Asset> assets = await transform.primaryInputs.toList();
    List<String> sources = assets.map((Asset a) => a.id.path).toList();
    String package = assets[0].id.package;
    Directory temp =
        await Directory.systemTemp.createTemp('fuchsia-dart-build');
    for (Asset a in assets) {
      transform.consumePrimary(a.id);
    }
    Asset fuchsiaAsset;
    if (flutter) {
      fuchsiaAsset = await applyFlutter(package, sources[0], temp.path);
    } else {
      fuchsiaAsset = await applyDart(package, sources[0], temp.path);
    }
    transform.addOutput(fuchsiaAsset);
    await temp.delete(recursive: true);
  }

  Future<Asset> applyDart(String package, String mainSource, String tempPath) async {
    String dartx = '$tempPath/$package.dartx';
    List<String> args = ['--packages=.packages', '--dartx=$dartx', mainSource];
    await runProcess('${paths.hostOut}/dart_snapshotter', args);
    return new Asset.fromBytes(
        new AssetId(package, 'fuchsia/$package.dartx'),
        new File(dartx).readAsBytesSync());
  }

  Future<Asset> applyFlutter(String package, String mainSource, String tempPath) async {
    String snapshot = "$tempPath/snapshot.bin";
    String bundle = "$tempPath/bundle.flx";

    await runProcess("${paths.hostOut}/sky_snapshot", [
      '--packages=.packages',
      '--snapshot=$snapshot',
      mainSource
    ]);

    await runProcess("${paths.fuchsiaRoot}/flutter/build/package.py", [
      "--root",
      paths.hostOut,
      "--flutter-root",
      "${paths.fuchsiaRoot}/lib/flutter",
      "--dart",
      "${paths.hostOut}/dart_no_observatory",
      "--flutter-tools-packages",
      "${paths.targetOut}/gen/lib/flutter/packages/flutter_tools/flutter_tools.packages",
      "--flutter-tools-main",
      "${paths.fuchsiaRoot}/lib/flutter/packages/flutter_tools/bin/fuchsia_builder.dart",
      "--working-dir",
      "$tempPath/working-dir",
      "--app-dir",
      ".",
      "--packages",
      ".packages",
      "--output-file",
      bundle,
      "--snapshot",
      snapshot
    ]);

    return new Asset.fromBytes(
        new AssetId(package, 'fuchsia/$package.flx'),
        new File(bundle).readAsBytesSync());
  }
}
