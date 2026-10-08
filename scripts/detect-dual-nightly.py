"""Resolve immutable upstream commits before any build starts."""
import importlib.util, json, os, re, urllib.error
from pathlib import Path
spec = importlib.util.spec_from_file_location('release_detector', Path(__file__).with_name('detect-nightly.py'))
detector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detector)

def nightly_tag(version, remix, gplall, recipe):
    for commit in (remix, gplall):
        if not re.fullmatch('[0-9a-f]{40}', commit):
            raise ValueError('Expected an immutable full commit SHA')
    return f'v{version}-nightly-{remix[:12]}-{gplall[:12]}-{recipe}'

def main():
    remix = detector.api('repos/NVIDIAGameWorks/dxvk-remix/commits/main')['sha']
    repo = detector.api('repos/Digger1955/dxvk-gplall')
    branch = repo['default_branch']
    from urllib.parse import quote
    gplall = detector.api('repos/Digger1955/dxvk-gplall/commits/' + quote(branch, safe=''))['sha']
    tag = nightly_tag(detector.source_version(Path('.')), remix, gplall, detector.recipe_fingerprint(Path('.')))
    pending = True
    if os.environ.get('FORCE_REBUILD', 'false').lower() != 'true':
        try:
            pending = not detector.release_complete(detector.api('repos/'+os.environ['GITHUB_REPOSITORY']+'/releases/tags/'+tag), tag)
        except urllib.error.HTTPError as error:
            if error.code != 404: raise
    metadata = {'name':'DXVK-GPLALL','version':'nightly-'+gplall[:12], 'variant':'GCC-SSE2-O3-LTO-source',
                'source_commit':gplall, 'source_branch':branch, 'source_repository':repo['html_url'],
                'release':repo['html_url']+'/commit/'+gplall}
    Path('nightly-backend.json').write_text(json.dumps(metadata, indent=2)+'\n')
    values = {'commit':remix,'gplall_commit':gplall,'gplall_branch':branch,'tag':tag,'version':tag[1:],'pending':str(pending).lower()}
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        for key, value in values.items(): output.write(key+'='+value+'\n')
    print(json.dumps(values, indent=2))
if __name__ == '__main__': main()
