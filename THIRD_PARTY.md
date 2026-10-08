# Third-party attribution

Nightly client and matching Host are compiled from NVIDIA dxvk-remix with the complete MIT L4D2 v1.1 adaptation patch from yeyunyyds/L4D2_Dxvk_32to64_Bridge, source snapshot 6c6dc09d7b1053f304ff6d7b353edadb46d6ca78. Preparation and backend packaging follow YuuMJ/L4D2_Dxvk_32to64_Bridge-Nightlybuild recipe snapshot 030c3b6dde55bf288c7c47fe84381c1569ef995e. Original yeyunyyds copyright notices remain intact.

The fixed-backend channel uses the unmodified DXVK-GPLALL 2.6.8-2 x64 GCC SSE2 O3 LTO release, with its download URL and archive SHA256 pinned in config/backend.json. The source Nightly channel builds x64 GPLALL from an explicitly recorded upstream commit. Both retain the zlib/libpng license. Packages record the actual backend in BACKEND.json and dependencies.json, their source revisions in UPSTREAM.json, and file checksums in SHA256.json.

NVIDIA Bridge MIT and bundled third-party notices, DXVK and GPLALL notices must accompany redistribution. See licenses and third_party/l4d2-bridge/THIRD_PARTY.md. This builds only Bridge, not the RTX Remix path-tracing renderer.

The root dependencies.json retains the historical L4D2 Bridge v1.1.0 / official DXVK 2.6.1 prototype references. Current manual packaging builds the YR-named runtime from source and does not use that historical manifest; the dependencies.json inside each generated package describes its actual backend.

Game files, cnc-ddraw, Ares, Phobos, Syringe and Steam are not bundled.
