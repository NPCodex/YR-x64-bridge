import hashlib,json,os,re,urllib.request,urllib.error
from pathlib import Path
def api(path):
    request=urllib.request.Request('https://api.github.com/'+path,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'User-Agent':'YR-MO-nightly'})
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
ref=os.environ.get('UPSTREAM_COMMIT','').strip() or 'main'
if ref!='main' and not re.fullmatch('[0-9a-fA-F]{40}',ref):raise ValueError('Use full 40-character SHA')
info=api('repos/NVIDIAGameWorks/dxvk-remix/commits/'+ref)
commit=info['sha']
backend=json.loads(Path('config/backend.json').read_text(encoding='utf-8-sig'))
fingerprint=hashlib.sha256(Path('config/backend.json').read_bytes()+Path('third_party/l4d2-bridge/patches/l4d2-bridge.patch').read_bytes()).hexdigest()[:8]
tag='nightly-'+info['commit']['committer']['date'][:10].replace('-','')+'-'+commit[:8]+'-gplall-'+backend['version']+'-'+fingerprint
pending=True
if os.environ.get('FORCE_REBUILD','false').lower()!='true':
    try:
        release=api('repos/'+os.environ['GITHUB_REPOSITORY']+'/releases/tags/'+tag)
        pending=release['draft'] or not any(a['name'].endswith('.zip') for a in release['assets'])
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
with open(os.environ['GITHUB_OUTPUT'],'a') as output:
    for key,value in {'commit':commit,'tag':tag,'pending':str(pending).lower()}.items():output.write(key+'='+value+'\n')
print('Upstream:',commit,'Release:',tag,'Build needed:',pending)
