import hashlib,json,os,re,subprocess,urllib.request,urllib.error
from pathlib import Path
def api(path):
    request=urllib.request.Request('https://api.github.com/'+path,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'User-Agent':'YR-MO-nightly'})
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
def recipe_fingerprint(root):
    paths=set()
    for directory in ['config','scripts','third_party/l4d2-bridge/scripts','third_party/l4d2-bridge/patches','third_party/l4d2-bridge/tests','.github/workflows']:
        paths.update(p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    digest=hashlib.sha256()
    for path in sorted(paths):
        name=path.relative_to(root).as_posix().encode()
        data=path.read_bytes().replace(b'\r\n',b'\n')
        digest.update(len(name).to_bytes(4,'big')+name+len(data).to_bytes(8,'big')+data)
    return digest.hexdigest()[:12]

def release_complete(release,tag):
    name='YR-MO-DXVK64-Bridge-v'+tag.removeprefix('v')+'.zip'
    assets={a['name']:a for a in release.get('assets',[])}
    return not release.get('draft',True) and all(assets.get(n,{}).get('size',0)>0 for n in [name,name+'.sha256'])

def version_from_distance(base,distance):
    major,minor=map(int,base.split('.'))
    return str(major)+'.'+str(minor+max(0,distance-1))

def source_version(root):
    settings=json.loads((root/'state/versioning.json').read_text())
    distance=int(subprocess.check_output(['git','rev-list','--count',settings['anchor_commit']+'..HEAD'],cwd=root,text=True))
    return version_from_distance(settings['base_version'],distance)

def main():
    ref=os.environ.get('UPSTREAM_COMMIT','').strip() or 'main'
    if ref!='main' and not re.fullmatch('[0-9a-fA-F]{40}',ref):raise ValueError('Use full 40-character SHA')
    info=api('repos/NVIDIAGameWorks/dxvk-remix/commits/'+ref)
    commit=info['sha']
    backend=json.loads(Path('config/backend.json').read_text(encoding='utf-8-sig'))
    fingerprint=recipe_fingerprint(Path('.'))
    version=source_version(Path('.'))
    tag='v'+version
    if os.environ.get('GITHUB_EVENT_NAME')=='schedule':
        tag+='-nightly-'+commit[:8]+'-'+fingerprint
    pending=True
    if os.environ.get('FORCE_REBUILD','false').lower()!='true':
        try:
            release=api('repos/'+os.environ['GITHUB_REPOSITORY']+'/releases/tags/'+tag)
            pending=not release_complete(release,tag)
        except urllib.error.HTTPError as error:
            if error.code!=404:raise
    with open(os.environ['GITHUB_OUTPUT'],'a') as output:
        for key,value in {'commit':commit,'tag':tag,'version':tag.removeprefix('v'),'pending':str(pending).lower()}.items():output.write(key+'='+value+'\n')
    print('Upstream:',commit,'Release:',tag,'Build needed:',pending)

if __name__=='__main__': main()
