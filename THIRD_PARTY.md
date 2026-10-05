# Third-party attribution

| Component | Source / version | License |
| --- | --- | --- |
| L4D2 Bridge adaptations | yeyunyyds/L4D2_Dxvk_32to64_Bridge, v1.1.0; source snapshot 6c6dc09d7b1053f304ff6d7b353edadb46d6ca78 | MIT, original Copyright (c) 2026 yeyunyyds retained |
| NVIDIA RTX Remix Bridge foundation | NVIDIAGameWorks/dxvk-remix, 9aa74f8dfad2188efbd0f717c64d9f8fa909787e | Bridge MIT and bundled third-party notices |
| Official DXVK D3D9 backend | doitsujin/dxvk, v2.6.1, unmodified | zlib/libpng |

This project adds YR/MO configuration and packaging. The shipped client and Host are upstream published binaries, not newly compiled or claimed as original work. Their L4D2 names are retained to preserve the loading protocol. The exact dependency URLs, source revisions and archive hashes are in dependencies.json. Package file hashes are in SHA256.json.

The full L4D2 adaptation patch, preparation/build scripts and tests are retained under third_party/l4d2-bridge. Its prepare_bridge.py fetches the pinned NVIDIA foundation and Detours dependency; it does not fetch the RTX renderer. All notices in licenses/ must accompany binary redistribution. Additional upstream references, credits and license boundaries remain in third_party/l4d2-bridge/THIRD_PARTY.md.

Nightly reference: https://github.com/YuuMJ/L4D2_Dxvk_32to64_Bridge-Nightlybuild. This release does not ship its DXVK-GPLALL backend or Nightly binaries.

cnc-ddraw is required separately and is not bundled in this release. Game executables, game resources, Ares, Phobos, Syringe, Steam and other mod files are not distributed.
