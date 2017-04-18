# I Can't Believe It's Not SDK

This isn't an SDK but it is a fairly practical way to build Fuchsia software out of tree. It's really most useful for
porting legacy software.

This is not an official Google product.

## Build

Add the manifest to your Fuchsia checkout with jiri:
```
jiri import -name=sdk-manifest sdk https://github.com/ianloic/fuchsia-sdk-manifest.git
jiri update
```

Include the sdk in your build:
```
packages/gn/gen.py --modules=default,../../sdk/module
```

Then do a build...

The SDK build relies on the packages/gn/desc.py script, which hard-codes debug,
so the build should be a debug build.

## Outputs

The build produces the following outputs in an `sdk` directory under your output directory, for example
`//out/debug-x86-64/sdk/`:
 * `lib/libfuchsia.a` -- a static library that links in everything from the Fuchsia tree that a C++ app that uses Modular,
   FIDL and Mozart might want, except those libraries in Fuchsia's sysroot (ie, libmagenta, libmxio, ...).
 * `include/**` -- all includes required to make use of `libfuchsia.a`, minus those found in the Fuchsia sysroot.
 * `fuchsia.makevars` -- a file that can be included in a Makefile that sets CC, CXX, LD, CFLAGS, CXXFLAGS, LDFLAGS and
   LIBS appropriately.

## TODO
 * Generate files to help building with autoconf, CMake, directly in the shell
 * Generate pkg-config directory for use w/ autoconf

