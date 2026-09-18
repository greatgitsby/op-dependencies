# Spectra camera UAPI

`comma-deps-spectra-uapi` packages two independent camera header snapshots for
openpilot's dual camera ABI work. The wheel is header-only (`py3-none-any`);
compiling consumers requires Linux userspace headers and GCC or Clang. Packaging
and the integrity smoketest also work on macOS.

| Include key | Source | Revision |
| --- | --- | --- |
| `agnos` | [commaai/agnos-kernel-sdm845](https://github.com/commaai/agnos-kernel-sdm845/tree/c368754c26c7b9659de187addc6cccedc6cfb0a0/include/uapi/media) | `c368754c26c7b9659de187addc6cccedc6cfb0a0` |
| `camera_kt` | [qualcomm-linux/camera-driver v1.0.3](https://github.com/qualcomm-linux/camera-driver/tree/56b463cba50c1db1f2cc53ddd8790730f14bd8a8/camera_kt/include/uapi/camera/media) | `56b463cba50c1db1f2cc53ddd8790730f14bd8a8` |

The legacy pin is the kernel submodule in agnos-builder commit
`ec1cf237a84565a056dbbc6f433b1b1c20c07a2c`. It supplies the 12 Spectra `cam_*.h`
headers plus `msm_camsensor_sdk.h`, used by the existing sensor code. The modern
set contains all 17 camera_kt camera UAPI headers. These are build snapshots;
they do not establish which driver revision is deployed on any device.

`spectra_uapi/sources.json` records the original paths, full source revisions,
and SHA-256 of every installed header and upstream license. `build.py` downloads
only those files, validates their hashes, and installs them **verbatim** under
`install/<abi>/include/media`. A verified download cache permits offline rebuilds.
There are no bundled generic Linux headers, ION/DMA-heap headers, private driver
headers, runtime detection, or driver changes.

The legacy tree's `COPYING` includes GPLv2 and its userspace syscall notice.
Modern headers retain their `GPL-2.0-only WITH Linux-syscall-note` identifiers
and copyright notices; its upstream `LICENSE.txt` is installed alongside them.
The syscall exception text is pinned separately to Linux v6.18 commit
`7d0a66e4bb9081d75c82ec4957c50034cb0ea449` in the same source manifest.
See `install/<abi>/licenses` and the pinned upstream source for licensing.

## Consumer integration

Compile each adapter in a separate translation unit with only its include root.
The identical upstream include guards and type names make including both sets
in one translation unit invalid. In C++ also isolate the camera types in private
namespaces (after including system headers globally), as the ABI test does, to
avoid conflicting type definitions across translation units. Share only
ABI-independent interfaces between adapters; link the resulting objects into
the same program.

```python
import spectra_uapi

legacy = env.Clone()
legacy.PrependUnique(CPPPATH=[spectra_uapi.INCLUDE_DIRS["agnos"]])
legacy.Append(CCFLAGS=["-include", spectra_uapi.COMPAT_HEADERS["agnos"]])

modern = env.Clone()
modern.PrependUnique(CPPPATH=[spectra_uapi.INCLUDE_DIRS["camera_kt"]])
modern.Append(CCFLAGS=["-include", spectra_uapi.COMPAT_HEADERS["camera_kt"]])
```

The legacy compatibility header supplies `<stdint.h>` and the empty `__user`
annotation normally removed by `headers_install`. The modern compatibility
header supplies `__DECLARE_FLEX_ARRAY` only when the host Linux headers lack it.
Both include `<time.h>` for C consumers of `<linux/videodev2.h>`. Clang builds
using `-Werror` also need `-Wno-gnu-variable-sized-type-not-at-end` for upstream
flexible-array extensions. No layouts or field types are patched.

## Validation

From the repository root:

```sh
uv build --package comma-deps-spectra-uapi --out-dir dist
uv venv /tmp/spectra-test
uv pip install --python /tmp/spectra-test/bin/python dist/comma_deps_spectra_uapi-*.whl
/tmp/spectra-test/bin/python -c 'import spectra_uapi; spectra_uapi.smoketest()'
/tmp/spectra-test/bin/python spectra-uapi/tests/test_headers.py
python spectra-uapi/tests/test_build.py
```

The compiler tests validate all headers independently in GNU C11 and C++17,
check camera command constants and representative sizes/offsets, serialize
sensor commands and decode frame events, and link both ABI objects into one
executable. They also reject swapped include roots and exercise the modern
compatibility fallback. Set `CC`/`CXX` to select the compilers.

These checks do not replace adapter integration or sustained capture, restart,
and flush testing on both driver stacks.
