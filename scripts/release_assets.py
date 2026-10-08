"""Shared integrity checks and recoverable GitHub release publication."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request


CHECKSUM_LIMIT = 4096


def api(path, method='GET', data=None):
    body = None if data is None else json.dumps(data).encode('utf-8')
    request = urllib.request.Request(
        'https://api.github.com/' + path, data=body, method=method,
        headers={
            'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
            'User-Agent': 'YR-MO-release',
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
            'X-GitHub-Api-Version': '2022-11-28',
        })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


class _AssetRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, new_url):
        redirected = super().redirect_request(request, fp, code, msg, headers, new_url)
        if redirected is not None:
            if urllib.parse.urlparse(new_url).scheme != 'https':
                raise ValueError('Asset download redirected outside HTTPS')
            if urllib.parse.urlparse(new_url).netloc != urllib.parse.urlparse(request.full_url).netloc:
                redirected.remove_header('Authorization')
        return redirected


def open_asset(asset):
    url = asset['url']
    if not re.fullmatch(r'https://api\.github\.com/repos/[^/]+/[^/]+/releases/assets/[0-9]+', url):
        raise ValueError('Unexpected GitHub asset API URL')
    request = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
        'Accept': 'application/octet-stream', 'User-Agent': 'YR-MO-release',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    return urllib.request.build_opener(_AssetRedirect()).open(request, timeout=60)


def read_checksum_asset(asset):
    with open_asset(asset) as response:
        content = response.read(CHECKSUM_LIMIT + 1)
    if len(content) > CHECKSUM_LIMIT:
        raise ValueError('Checksum asset is too large')
    return content


def archive_name(tag):
    if not re.fullmatch(r'v?[0-9A-Za-z][0-9A-Za-z.+-]*', tag):
        raise ValueError('Invalid release tag')
    return 'YR-MO-DXVK64-Bridge-v' + tag.removeprefix('v') + '.zip'


def checksum_digest(content, filename):
    if not content or len(content) > CHECKSUM_LIMIT:
        raise ValueError('Invalid checksum file size')
    match = re.fullmatch(r'([0-9a-fA-F]{64}) [ *]' + re.escape(filename) + r'\r?\n?', content.decode('utf-8-sig'))
    if match is None:
        raise ValueError('Checksum must name the exact release archive')
    return match.group(1).lower()


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def asset_pair(release, tag):
    assets = release.get('assets', [])
    names = (archive_name(tag), archive_name(tag) + '.sha256')
    pair = []
    for name in names:
        matches = [asset for asset in assets if asset.get('name') == name]
        if len(matches) != 1 or matches[0].get('size', 0) <= 0 or matches[0].get('state') != 'uploaded':
            raise ValueError('Release asset missing, empty, duplicated or not uploaded: ' + name)
        pair.append(matches[0])
    if pair[1]['size'] > CHECKSUM_LIMIT:
        raise ValueError('Checksum asset is too large')
    return pair


def github_digest(asset):
    value = asset.get('digest') or ''
    if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}', value):
        # Rebuild legacy assets once instead of downloading the full archive
        # on every hourly detection run to guess whether it is complete.
        raise ValueError('Release archive has no GitHub SHA256 digest')
    return value.split(':', 1)[1].lower()


def release_complete(release, tag, read_checksum=None):
    if release.get('draft', True):
        return False
    try:
        archive, checksum = asset_pair(release, tag)
        expected = github_digest(archive)
        content = (read_checksum or read_checksum_asset)(checksum)
        return len(content) == checksum['size'] and checksum_digest(content, archive['name']) == expected
    except ValueError:
        return False
    # HTTP/auth/rate-limit/network failures fail detection, not trigger a build.


def local_pair(directory, tag):
    archive = Path(directory) / archive_name(tag)
    checksum = archive.with_name(archive.name + '.sha256')
    if not archive.is_file() or archive.stat().st_size == 0:
        raise ValueError('Missing or empty local release archive')
    if checksum.stat().st_size > CHECKSUM_LIMIT:
        raise ValueError('Local checksum file is too large')
    expected = checksum_digest(checksum.read_bytes(), archive.name)
    if file_digest(archive) != expected:
        raise ValueError('Local release checksum mismatch')
    return archive, checksum, expected


class GitHubReleaseClient:
    def __init__(self, repository):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('Invalid GitHub repository')
        self.repository = repository
        self.path = 'repos/' + repository + '/releases'

    def get_release(self, tag):
        try:
            return api(self.path + '/tags/' + urllib.parse.quote(tag, safe=''))
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
        # GitHub's tag endpoint may omit drafts. Paginate to recover an
        # interrupted publication instead of trying to create a duplicate tag.
        page = 1
        while True:
            releases = api(self.path + '?per_page=100&page=' + str(page))
            for release in releases:
                if release['tag_name'] == tag:
                    return release
            if len(releases) < 100:
                return None
            page += 1

    def create_draft(self, tag, target, notes):
        return api(self.path, 'POST', {
            'tag_name': tag, 'target_commitish': target, 'name': tag,
            'body': notes, 'draft': True, 'prerelease': '-nightly-' in tag,
        })

    def edit_release(self, release_id, **fields):
        return api(self.path + '/' + str(release_id), 'PATCH', fields)

    def upload_assets(self, tag, paths):
        subprocess.run(['gh', 'release', 'upload', tag, *map(str, paths),
                        '--clobber', '--repo', self.repository], check=True)

    def download_asset(self, asset, destination):
        with open_asset(asset) as response, Path(destination).open('wb') as stream:
            for block in iter(lambda: response.read(1024 * 1024), b''):
                stream.write(block)


def publish_release(client, tag, target, notes, directory):
    """Keep every incomplete replacement draft, including after interruption."""
    archive, checksum, expected = local_pair(directory, tag)
    release = client.get_release(tag)
    if release is None:
        release = client.create_draft(tag, target, notes)
    else:
        release = client.edit_release(release['id'], draft=True)
    if not release.get('draft', False):
        raise ValueError('Release must be draft before replacing assets')

    client.upload_assets(tag, (archive, checksum))
    uploaded = client.get_release(tag)
    if uploaded is None or not uploaded.get('draft', False) or uploaded['id'] != release['id']:
        raise ValueError('Release changed during upload')
    remote_archive, remote_checksum = asset_pair(uploaded, tag)
    if github_digest(remote_archive) != expected:
        raise ValueError('Uploaded archive digest differs from the local archive')
    with tempfile.TemporaryDirectory(prefix='yr-release-verify-') as temporary:
        for asset, local in ((remote_archive, archive), (remote_checksum, checksum)):
            downloaded = Path(temporary) / local.name
            client.download_asset(asset, downloaded)
            if downloaded.stat().st_size != asset['size'] or file_digest(downloaded) != file_digest(local):
                raise ValueError('Downloaded release asset differs from the local file: ' + local.name)
        local_pair(temporary, tag)

    result = client.edit_release(release['id'], draft=False, prerelease='-nightly-' in tag, body=notes)
    if result.get('draft', True):
        raise ValueError('GitHub did not publish the verified release')
    return result
