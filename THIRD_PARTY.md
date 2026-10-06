# Third-party attribution

Nightly client and matching Host are compiled from NVIDIA dxvk-remix with the complete MIT L4D2 v1.1 adaptation patch from yeyunyyds/L4D2_Dxvk_32to64_Bridge, source snapshot 6c6dc09d7b1053f304ff6d7b353edadb46d6ca78. Preparation and backend packaging follow YuuMJ/L4D2_Dxvk_32to64_Bridge-Nightlybuild recipe snapshot 030c3b6dde55bf288c7c47fe84381c1569ef995e. Original yeyunyyds copyright notices remain intact.

Nightly backend: unmodified DXVK-GPLALL 2.6.8-2 x64, GCC SSE2 O3 LTO, zlib/libpng license. Download URL and archive SHA256 are fixed in config/backend.json. Published Nightly archives record UPSTREAM.json, BACKEND.json and SHA256.json.

NVIDIA Bridge MIT and bundled third-party notices, DXVK and GPLALL notices must accompany redistribution. See licenses and third_party/l4d2-bridge/THIRD_PARTY.md. This builds only Bridge, not the RTX Remix path-tracing renderer.

Legacy manual packaging uses L4D2 Bridge v1.1.0 and official DXVK 2.6.1 as pinned in the root dependencies.json. That file describes the legacy channel only.

Game files, cnc-ddraw, Ares, Phobos, Syringe and Steam are not bundled.
