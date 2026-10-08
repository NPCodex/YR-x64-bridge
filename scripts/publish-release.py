"""Publish only after local and downloaded release assets agree."""
import argparse
import os
from release_assets import GitHubReleaseClient, publish_release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', default='assets')
    args = parser.parse_args()
    tag = os.environ['TAG']
    gplall = os.environ.get('GPLALL_COMMIT', '')
    notes = ('YR/MO ' + ('Nightly' if '-nightly-' in tag else 'Release') + '\n\n'
             + 'NVIDIA commit: ' + os.environ['UPSTREAM_COMMIT'] + '\n'
             + ('GPLALL commit: ' + gplall + '\n' if gplall else '')
             + 'Recipe commit: ' + os.environ['RECIPE_COMMIT'] + '\n\n'
             + 'x86 d3d9.dll, matching x64 Host, '
             + ('source-built' if gplall else 'pinned') + ' GPLALL backend. '
             + 'Extract to game root. Compilation and diagnostics passed; game validation pending.\n')
    result = publish_release(GitHubReleaseClient(os.environ['GH_REPO']), tag,
                             os.environ['RECIPE_COMMIT'], notes, args.assets)
    print('Published verified release:', result['html_url'])


if __name__ == '__main__':
    main()
