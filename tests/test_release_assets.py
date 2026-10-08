"""Exercise interrupted uploads and downloaded corruption without GitHub writes."""
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import release_assets as releases


TAG = 'v1.2.3'
NAME = releases.archive_name(TAG)


def asset(name, content):
    return {'name': name, 'size': len(content), 'state': 'uploaded',
            'digest': 'sha256:' + hashlib.sha256(content).hexdigest()}


def checksum(content=b'new archive', name=NAME):
    return (hashlib.sha256(content).hexdigest() + '  ' + name + '\n').encode()


class FakeClient:
    def __init__(self, existing=True):
        self.events = []
        self.contents = {NAME: b'old archive', NAME + '.sha256': checksum(b'old archive')}
        self.release = {'id': 7, 'tag_name': TAG, 'draft': False, 'assets': [], 'html_url': 'https://example.test/release'} if existing else None
        self.interrupt_upload = False
        self.corrupt_download = None
        self.upload_corruption = None
        self.refuse_draft = False

    def get_release(self, tag):
        self.events.append('get')
        if self.release is not None:
            self.release['assets'] = [asset(name, content) for name, content in self.contents.items()]
        return copy.deepcopy(self.release)

    def create_draft(self, tag, target, notes):
        self.events.append('create draft')
        self.contents = {}
        self.release = {'id': 7, 'tag_name': tag, 'draft': True, 'assets': [], 'html_url': 'https://example.test/release'}
        return copy.deepcopy(self.release)

    def edit_release(self, release_id, **fields):
        self.events.append('draft' if fields['draft'] else 'publish')
        if not self.refuse_draft:
            self.release.update(fields)
        return copy.deepcopy(self.release)

    def upload_assets(self, tag, paths):
        if not self.release['draft']:
            raise AssertionError('Uploading to a public release')
        for path in paths:
            self.events.append('upload ' + path.name)
            self.contents[path.name] = path.read_bytes()
            if self.upload_corruption == path.name:
                self.contents[path.name] = b'corrupted upload'
            if self.interrupt_upload:
                raise OSError('Upload interrupted after replacing ZIP')

    def download_asset(self, remote, destination):
        self.events.append('download ' + remote['name'])
        content = self.contents[remote['name']]
        if self.corrupt_download == remote['name']:
            content = b'corrupt' + content
        Path(destination).write_bytes(content)


class ReleaseCompletenessTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()
        self.release = self.client.get_release(TAG)

    def complete(self):
        return releases.release_complete(self.release, TAG, lambda item: self.client.contents[item['name']])

    def test_old_checksum_with_new_archive_is_incomplete(self):
        self.client.contents[NAME] = b'new archive'
        self.release = self.client.get_release(TAG)
        self.assertFalse(self.complete())

    def test_valid_pair_needs_only_the_small_checksum(self):
        fetched = []
        def read(item):
            fetched.append(item['name'])
            return self.client.contents[item['name']]
        self.assertTrue(releases.release_complete(self.release, TAG, read))
        self.assertEqual(fetched, [NAME + '.sha256'])

    def test_draft_never_downloads_or_counts_as_complete(self):
        self.release['draft'] = True
        self.assertFalse(releases.release_complete(self.release, TAG, lambda _: self.fail('Draft downloaded')))

    def test_legacy_missing_digest_requires_one_rebuild_without_download(self):
        self.release['assets'][0].pop('digest')
        self.assertFalse(releases.release_complete(self.release, TAG, lambda _: self.fail('Legacy ZIP downloaded')))

    def test_bad_checksum_filename_and_multiple_entries_are_rejected(self):
        for content in (checksum(b'old archive', 'other.zip'), checksum(b'old archive') * 2, b'\xff'):
            self.client.contents[NAME + '.sha256'] = content
            self.release = self.client.get_release(TAG)
            self.assertFalse(self.complete())

    def test_duplicate_incomplete_empty_and_large_assets_are_rejected(self):
        for change in ('duplicate', 'starter', 'empty', 'large'):
            with self.subTest(change=change):
                self.release = self.client.get_release(TAG)
                if change == 'duplicate':
                    self.release['assets'].append(self.release['assets'][0])
                elif change == 'starter':
                    self.release['assets'][0]['state'] = 'starter'
                elif change == 'empty':
                    self.release['assets'][0]['size'] = 0
                else:
                    self.release['assets'][1]['size'] = releases.CHECKSUM_LIMIT + 1
                self.assertFalse(self.complete())

    def test_network_errors_are_not_missing_release(self):
        for code in (403, 404, 429, 500):
            with self.subTest(code=code):
                error = urllib.error.HTTPError('https://example.test', code, 'error', {}, None)
                with patch.object(releases, 'read_checksum_asset', side_effect=error):
                    with self.assertRaises(urllib.error.HTTPError):
                        releases.release_complete(self.release, TAG)

    def test_windows_checksum_and_binary_marker_are_accepted(self):
        content = checksum().replace(b'  ', b' *').replace(b'\n', b'\r\n')
        self.assertEqual(releases.checksum_digest(content, NAME), hashlib.sha256(b'new archive').hexdigest())


class ReleasePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        (self.directory / NAME).write_bytes(b'new archive')
        (self.directory / (NAME + '.sha256')).write_bytes(checksum())
        self.client = FakeClient()

    def publish(self):
        return releases.publish_release(self.client, TAG, 'recipe', 'release notes', self.directory)

    def test_bad_local_checksum_leaves_public_release_untouched(self):
        (self.directory / (NAME + '.sha256')).write_bytes(checksum(b'wrong archive'))
        with self.assertRaisesRegex(ValueError, 'Local release checksum mismatch'):
            self.publish()
        self.assertEqual(self.client.events, [])
        self.assertFalse(self.client.release['draft'])

    def test_existing_release_is_draft_until_both_downloads_are_verified(self):
        result = self.publish()
        self.assertFalse(result['draft'])
        self.assertEqual(self.client.events, ['get', 'draft', 'upload ' + NAME,
                         'upload ' + NAME + '.sha256', 'get', 'download ' + NAME,
                         'download ' + NAME + '.sha256', 'publish'])
        self.assertFalse(result['prerelease'])

    def test_new_release_starts_as_draft(self):
        self.client = FakeClient(existing=False)
        self.publish()
        self.assertEqual(self.client.events[1], 'create draft')

    def test_interrupted_replacement_is_detectable_and_recovers(self):
        self.client.interrupt_upload = True
        with self.assertRaises(OSError):
            self.publish()
        self.assertTrue(self.client.release['draft'])
        self.assertNotIn('publish', self.client.events)
        self.assertFalse(releases.release_complete(self.client.get_release(TAG), TAG))
        self.client.interrupt_upload = False
        self.publish()
        self.assertFalse(self.client.release['draft'])
        self.assertEqual(self.client.contents[NAME + '.sha256'], checksum())

    def test_draft_transition_must_succeed_before_upload(self):
        self.client.refuse_draft = True
        with self.assertRaisesRegex(ValueError, 'must be draft'):
            self.publish()
        self.assertEqual(self.client.events, ['get', 'draft'])

    def test_corrupted_downloads_are_never_published(self):
        for name in (NAME, NAME + '.sha256'):
            with self.subTest(asset=name):
                self.client = FakeClient()
                self.client.corrupt_download = name
                with self.assertRaisesRegex(ValueError, 'Downloaded release asset differs'):
                    self.publish()
                self.assertTrue(self.client.release['draft'])
                self.assertNotIn('publish', self.client.events)

    def test_wrong_server_archive_digest_is_never_published(self):
        self.client.upload_corruption = NAME
        with self.assertRaisesRegex(ValueError, 'Uploaded archive digest differs'):
            self.publish()
        self.assertTrue(self.client.release['draft'])
        self.assertNotIn('publish', self.client.events)


class GitHubClientTests(unittest.TestCase):
    def test_draft_fallback_and_pagination(self):
        error = urllib.error.HTTPError('https://example.test', 404, 'missing', {}, None)
        draft = {'id': 9, 'tag_name': TAG, 'draft': True}
        pages = [error, [{'tag_name': 'other'}] * 100, [draft]]
        with patch.object(releases, 'api', side_effect=pages) as api:
            self.assertEqual(releases.GitHubReleaseClient('owner/repo').get_release(TAG), draft)
            self.assertTrue(api.call_args.args[0].endswith('page=2'))

    def test_only_actual_404_allows_missing_release(self):
        for code in (403, 429, 500):
            with self.subTest(code=code):
                error = urllib.error.HTTPError('https://example.test', code, 'error', {}, None)
                with patch.object(releases, 'api', side_effect=error) as api:
                    with self.assertRaises(urllib.error.HTTPError):
                        releases.GitHubReleaseClient('owner/repo').get_release(TAG)
                    self.assertEqual(api.call_count, 1)
        error = urllib.error.HTTPError('https://example.test', 404, 'missing', {}, None)
        with patch.object(releases, 'api', side_effect=[error, []]):
            self.assertIsNone(releases.GitHubReleaseClient('owner/repo').get_release(TAG))

    def test_asset_redirect_does_not_forward_token(self):
        request = urllib.request.Request('https://api.github.com/asset', headers={'Authorization': 'Bearer test'})
        redirected = releases._AssetRedirect().redirect_request(request, None, 302, 'Found', {}, 'https://release-assets.githubusercontent.com/asset')
        self.assertFalse(redirected.has_header('Authorization'))


if __name__ == '__main__':
    unittest.main()
