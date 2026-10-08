"""Offline packaging regressions using tiny synthetic PE files."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "package_release", REPO / "third_party/l4d2-bridge/scripts/package_release.py")
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def pe(machine, marker=b""):
    data = bytearray(128)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 60, 64)
    data[64:68] = b"PE\0\0"
    struct.pack_into("<H", data, 68, machine)
    return bytes(data) + marker


class Packaging(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="yr-package-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.vendor = self.root / "vendor"
        self.source = self.root / "source"
        self.dxvk = self.root / "backend/d3d9.dll"
        self.output = self.root / "intermediate/l4d2-bridge"
        self.client_output = self.output.parent / "l4d2-client-only"
        for relative in ("README.md", "LICENSE", "THIRD_PARTY.md", "config/bridge.conf",
                         "docs/TESTING.md", "docs/MEMORY-DIAGNOSTICS.md",
                         "docs/FIRST-GAME-VALIDATION.md", "patches/l4d2-bridge.patch",
                         "licenses/DXVK-LICENSE.txt", "licenses/DXVK-GPLALL-LICENSE.txt"):
            write(self.vendor / relative, relative)
        write(self.vendor / "VERSION", "1.0.0")
        write(self.source / "bridge/_compDebugOptimized_x86/src/client/d3d9.dll", pe(0x14c))
        write(self.source / "bridge/_compDebugOptimized_x64/src/server/YRBridge64.exe", pe(0x8664))
        write(self.source / "bridge/LICENSE-MIT", "bridge license")
        write(self.source / "bridge/ThirdPartyLicenses.txt", "third-party licenses")
        write(self.dxvk, pe(0x8664, b"current backend"))
        self.digest = hashlib.sha256(self.dxvk.read_bytes()).hexdigest()
        self.metadata = self.dxvk.with_name("source-backend.json")
        write(self.metadata, json.dumps({"name": "DXVK-GPLALL", "sha256": self.digest,
                                        "commit": "a" * 40, "release": "source nightly"}))
        write(self.dxvk.with_name("DXVK-GPLALL-LICENSE.txt"), "source license")
        self.root_patch = patch.object(PACKAGER, "ROOT", self.vendor)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def package(self, metadata=None):
        with contextlib.redirect_stdout(io.StringIO()):
            PACKAGER.package(self.source, self.dxvk, self.output, metadata,
                             upstream_commit="b" * 40, recipe_commit="c" * 40)

    def assert_clean(self):
        self.assertFalse(self.output.exists())
        self.assertFalse(self.client_output.exists())
        self.assertEqual(list(self.output.parent.glob(".package-*")), [])

    def stale_source_cache(self):
        write(self.vendor / ".deps/gplall/source-backend.json", "not even valid JSON")

    def test_custom_backend_ignores_stale_source_cache(self):
        self.stale_source_cache()
        self.package()
        metadata = json.loads((self.output / "BACKEND.json").read_text())
        self.assertEqual(metadata, {"sha256": self.digest, "architecture": "x86_64",
                                    "source": "custom -DxvkDll"})

    def test_pinned_backend_matches_verified_archive_not_extracted_cache(self):
        self.stale_source_cache()
        archive = self.vendor / ".deps/gplall/backend.zip"
        with zipfile.ZipFile(archive, "w") as release:
            release.writestr("x64/d3d9.dll", self.dxvk.read_bytes())
        archive_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        write(self.vendor / "config/backend.json", json.dumps({"name": "DXVK-GPLALL",
              "sha256": archive_digest, "release": "fixed release"}))
        write(self.vendor / ".deps/gplall/release/x64/d3d9.dll", b"damaged extracted cache")
        self.package()
        metadata = json.loads((self.output / "BACKEND.json").read_text())
        self.assertEqual(metadata["source"], "fixed release")
        self.assertEqual(metadata["sha256"], self.digest)
        self.assertEqual(metadata["archive_sha256"], archive_digest)

    def test_explicit_metadata_and_license_travel_with_this_package(self):
        self.stale_source_cache()
        self.package(self.metadata)
        metadata = json.loads((self.output / "BACKEND.json").read_text())
        self.assertEqual(metadata["commit"], "a" * 40)
        self.assertEqual(metadata["sha256"], self.digest)
        self.assertEqual((self.output / "licenses/DXVK-GPLALL-LICENSE.txt").read_text(), "source license")
        self.assertEqual((self.vendor / "licenses/DXVK-GPLALL-LICENSE.txt").read_text(),
                         "licenses/DXVK-GPLALL-LICENSE.txt")
        manifest = json.loads((self.output / "SHA256.json").read_text())
        for filename, expected in manifest.items():
            self.assertEqual(hashlib.sha256((self.output / filename).read_bytes()).hexdigest(), expected)
        self.assertIn("BACKEND.json", manifest)
        self.assertIn("UPSTREAM.json", manifest)

    def test_metadata_mismatch_creates_no_output_and_retry_succeeds(self):
        good_metadata = self.metadata.read_text()
        write(self.metadata, json.dumps({"sha256": "0" * 64}))
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            self.package(self.metadata)
        self.assert_clean()
        write(self.metadata, good_metadata)
        self.package(self.metadata)
        self.assertTrue(self.output.is_dir())

    def test_missing_explicit_license_creates_no_output(self):
        self.dxvk.with_name("DXVK-GPLALL-LICENSE.txt").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "Backend license"):
            self.package(self.metadata)
        self.assert_clean()

    def test_copy_failure_cleans_staging_and_retry_succeeds(self):
        missing = self.vendor / "docs/TESTING.md"
        missing.unlink()
        with self.assertRaises(FileNotFoundError):
            self.package()
        self.assert_clean()
        write(missing, "restored")
        self.package()
        self.assertTrue(self.output.is_dir())

    def test_second_output_failure_rolls_back_only_owned_output(self):
        rename = Path.rename

        def fail_client(candidate, destination):
            if destination == self.client_output:
                raise OSError("simulated second move failure")
            return rename(candidate, destination)

        with patch.object(Path, "rename", fail_client):
            with self.assertRaisesRegex(OSError, "second move"):
                self.package()
        self.assert_clean()
        self.package()
        self.assertTrue(self.client_output.is_dir())

    def test_existing_package_is_never_overwritten(self):
        for destination in (self.output, self.client_output):
            with self.subTest(destination=destination):
                write(destination / "keep.txt", "existing release")
                with self.assertRaises(FileExistsError):
                    self.package()
                self.assertEqual((destination / "keep.txt").read_text(), "existing release")
                shutil.rmtree(destination)

    def test_invalid_pe_leaves_no_partial_output(self):
        write(self.dxvk, b"MZ" + bytes(62))
        with self.assertRaisesRegex(ValueError, "Invalid PE signature"):
            self.package()
        self.assert_clean()

    def prepare_outer(self):
        self.package(self.metadata)
        self.outer = self.root / "outer"
        write(self.outer / "scripts/package.ps1", (REPO / "scripts/package.ps1").read_bytes())
        for filename in ("README.md", "LICENSE", "THIRD_PARTY.md", "config/bridge.conf", "VERSION"):
            write(self.outer / filename, (self.vendor / filename).read_bytes())
        write(self.outer / "docs/README.md", "documentation")
        write(self.outer / "dependencies.json", '{"source":"obsolete dependency"}')
        write(self.outer / "config/backend.json", '{"source":"obsolete fixed backend"}')
        write(self.outer / "third_party/l4d2-bridge/.deps/gplall/source-backend.json", '{"source":"obsolete nightly"}')
        self.outer_output = self.outer / "dist/YR-MO-DXVK64-Bridge-v1.0.0"
        self.outer_zip = self.outer_output.parent / (self.outer_output.name + ".zip")

    def run_outer(self):
        env = dict(os.environ, UPSTREAM_COMMIT="stale environment", GITHUB_SHA="stale recipe")
        return subprocess.run([POWERSHELL, "-NoProfile", "-File", str(self.outer / "scripts/package.ps1"),
                               "-BridgeDirectory", str(self.output)], capture_output=True,
                              encoding="utf-8", errors="replace", env=env)

    @unittest.skipUnless(POWERSHELL, "PowerShell is needed to exercise the final packager")
    def test_final_package_uses_runtime_provenance_and_valid_hashes(self):
        self.prepare_outer()
        result = self.run_outer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        backend = json.loads((self.outer_output / "BACKEND.json").read_text())
        self.assertEqual(json.loads((self.outer_output / "dependencies.json").read_text()), backend)
        upstream = json.loads((self.outer_output / "UPSTREAM.json").read_text())
        self.assertEqual(upstream["upstream_commit"], "b" * 40)
        self.assertEqual(upstream["recipe_commit"], "c" * 40)
        manifest = json.loads((self.outer_output / "SHA256.json").read_text(encoding="utf-8-sig"))
        with zipfile.ZipFile(self.outer_zip) as release:
            for filename, expected in manifest.items():
                self.assertEqual(hashlib.sha256(release.read(filename)).hexdigest(), expected)
        checksum = Path(str(self.outer_zip) + ".sha256").read_text()
        self.assertEqual(checksum, hashlib.sha256(self.outer_zip.read_bytes()).hexdigest() +
                         "  " + self.outer_zip.name + "\n")
        self.assertEqual(list(self.outer_output.parent.glob(".package-*")), [])

    @unittest.skipUnless(POWERSHELL, "PowerShell is needed to exercise the final packager")
    def test_final_package_copy_failure_is_retryable(self):
        self.prepare_outer()
        missing = self.outer / "README.md"
        missing.unlink()
        result = self.run_outer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("README.md", result.stderr)
        self.assertFalse(self.outer_output.exists())
        self.assertFalse(self.outer_zip.exists())
        self.assertEqual(list(self.outer_output.parent.glob(".package-*")), [])
        write(missing, "restored")
        result = self.run_outer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(POWERSHELL, "PowerShell is needed to exercise the final packager")
    def test_final_package_preserves_existing_checksum(self):
        self.prepare_outer()
        checksum = Path(str(self.outer_zip) + ".sha256")
        write(checksum, "existing release checksum")
        result = self.run_outer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Release output already exists", result.stderr)
        self.assertEqual(checksum.read_text(), "existing release checksum")
        self.assertFalse(self.outer_output.exists())
        self.assertFalse(self.outer_zip.exists())

    @unittest.skipUnless(POWERSHELL, "PowerShell is needed to exercise the final packager")
    def test_final_package_rejects_metadata_for_a_different_dll(self):
        self.prepare_outer()
        metadata = self.output / "BACKEND.json"
        write(metadata, json.dumps({"sha256": "0" * 64}))
        manifest_path = self.output / "SHA256.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["BACKEND.json"] = hashlib.sha256(metadata.read_bytes()).hexdigest()
        write(manifest_path, json.dumps(manifest))
        result = self.run_outer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Backend metadata checksum mismatch", result.stderr)
        self.assertFalse(self.outer_output.exists())
        self.assertFalse(self.outer_zip.exists())


if __name__ == "__main__":
    unittest.main()
