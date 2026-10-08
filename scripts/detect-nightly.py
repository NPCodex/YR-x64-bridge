import hashlib,json,os,re,subprocess,sys,urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_assets import api, release_complete
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

def version_from_messages(base,messages):
    parts=list(map(int,base.split('.')))
    major,minor=parts[:2]
    patch=parts[2] if len(parts)>2 else 0
    for message in messages[1:]:
        explicit=re.search(r'^Release-Level:\s*(major|minor|patch)\s*$',message,re.MULTILINE|re.IGNORECASE)
        level=explicit.group(1).lower() if explicit else ('minor' if re.match(r'feat(?:\([^)]*\))?:',message.strip()) else 'patch')
        if level=='major':major+=1;minor=patch=0
        elif level=='minor':minor+=1;patch=0
        else:patch+=1
    return str(major)+'.'+str(minor)+(('.'+str(patch)) if patch else '')

def source_version(root):
    settings=json.loads((root/'state/versioning.json').read_text())
    history=subprocess.check_output(['git','log','--reverse','--format=%B%x1e',settings['anchor_commit']+'..HEAD'],cwd=root,text=True,encoding='utf-8')
    messages=[m.strip() for m in history.split('\x1e') if m.strip()]
    return version_from_messages(settings['base_version'],messages)

def main():
    ref=os.environ.get('UPSTREAM_COMMIT','').strip() or 'main'
    if ref!='main' and not re.fullmatch('[0-9a-fA-F]{40}',ref):raise ValueError('Use full 40-character SHA')
    info=api('repos/NVIDIAGameWorks/dxvk-remix/commits/'+ref)
    commit=info['sha']
    fingerprint=recipe_fingerprint(Path('.'))
    version=source_version(Path('.'))
    tag='v'+version
    if os.environ.get('GITHUB_EVENT_NAME')=='schedule':
        tag+='-nightly-'+commit[:8]+'-'+fingerprint
    pending=True
    if os.environ.get('FORCE_REBUILD','false').lower()!='true':
        try:
            release=api('repos/'+os.environ['GITHUB_REPOSITORY']+'/releases/tags/'+tag)
        except urllib.error.HTTPError as error:
            if error.code!=404:raise
        else:
            pending=not release_complete(release,tag)
    with open(os.environ['GITHUB_OUTPUT'],'a') as output:
        for key,value in {'commit':commit,'tag':tag,'version':tag.removeprefix('v'),'pending':str(pending).lower()}.items():output.write(key+'='+value+'\n')
    print('Upstream:',commit,'Release:',tag,'Build needed:',pending)

if __name__=='__main__': main()
