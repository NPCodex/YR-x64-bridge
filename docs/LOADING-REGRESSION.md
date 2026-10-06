# Loading regression investigation — 2026-10-06

The user verified that stable Bridge v1.1 (NVIDIA foundation 9aa74f8d) plus GPLALL 2.6.8-2 loads maps quickly and plays normally. Thus x64 GPLALL 2.6.8 is usable on this system.

NVIDIA Bridge source is identical between 9aa74f8d and 418c3a12 (git diff --quiet over bridge returned 0). The failing Nightly uses a reduced adaptation patch, not the complete v1.1 patch. Removed features include queue wake/wait handling, resource retention, texture layout/readback work and diagnostics. Queue handling is a candidate cause, not a proven sole cause.

YR builds now retain the complete stable v1.1 adaptation patch while fetching the requested/latest NVIDIA commit. The patch applies cleanly to 418c3a12. Nightly packaging scripts remain in place because YR only requires x86 client + x64 Host. Stable diagnostic tests are retained.

Release fingerprint includes backend config and adaptation patch so this repair is rebuilt even if upstream commit is unchanged. New binaries still require cloud compilation and map-loading validation before a fix is claimed. Current game binaries remain the user's known-good stable Bridge + GPLALL combination.
