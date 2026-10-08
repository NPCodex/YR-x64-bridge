import hashlib,importlib.util,os,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('detect',Path(__file__).parents[1]/'scripts/detect-nightly.py')
detect=importlib.util.module_from_spec(spec);spec.loader.exec_module(detect)
class NightlyTests(unittest.TestCase):
    def test_version_sequence(self):
        initial=['release: v1.0']
        self.assertEqual(detect.version_from_messages('1.0',initial),'1.0')
        history=initial+['fix: first','docs: guide']
        self.assertEqual(detect.version_from_messages('1.0',history),'1.0.2')
        history+=['feat: new rendering feature','fix: compatibility']
        self.assertEqual(detect.version_from_messages('1.0',history),'1.1.1')
        history+=['refactor: major improvement\n\nRelease-Level: minor']
        self.assertEqual(detect.version_from_messages('1.0',history),'1.2')
    def test_explicit_release_level(self):
        self.assertEqual(detect.version_from_messages('1.0',['initial','feat: tiny option\nRelease-Level: patch']),'1.0.1')
    def test_complete_pair(self):
        name='YR-MO-DXVK64-Bridge-vtest.zip'
        digest=hashlib.sha256(b'zip').hexdigest()
        content=(digest+'  '+name+'\n').encode()
        release={'draft':False,'assets':[{'name':name,'size':3,'state':'uploaded','digest':'sha256:'+digest},
                                       {'name':name+'.sha256','size':len(content),'state':'uploaded'}]}
        self.assertTrue(detect.release_complete(release,'test',lambda asset:content))
        release['assets'].pop();self.assertFalse(detect.release_complete(release,'test'))
    def test_unrelated_and_empty_assets(self):
        self.assertFalse(detect.release_complete({'draft':False,'assets':[{'name':'other.zip','size':3}]},'test'))
        self.assertFalse(detect.release_complete({'draft':False,'assets':[]},'test'))
    def run_detector(self, lookup, completeness=True, force=False):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'output'
            environment={'GH_TOKEN':'test','GITHUB_REPOSITORY':'owner/repo','GITHUB_OUTPUT':str(output),
                         'FORCE_REBUILD':str(force).lower(),'UPSTREAM_COMMIT':'','GITHUB_EVENT_NAME':'push'}
            with patch.dict(os.environ,environment), patch.object(detect,'source_version',return_value='1.2.3'), \
                 patch.object(detect,'recipe_fingerprint',return_value='recipe'), \
                 patch.object(detect,'api',side_effect=[{'sha':'a'*40},lookup]) as api, \
                 patch.object(detect,'release_complete',side_effect=completeness if isinstance(completeness,Exception) else None,
                              return_value=completeness):
                detect.main()
                return output.read_text(),api.call_count
    def test_missing_release_is_pending(self):
        missing=urllib.error.HTTPError('url',404,'missing',{},None)
        output,_=self.run_detector(missing)
        self.assertIn('pending=true',output)
    def test_lookup_network_errors_and_checksum_404_do_not_trigger_build(self):
        for code in (403,429,500):
            with self.subTest(code=code),self.assertRaises(urllib.error.HTTPError):
                self.run_detector(urllib.error.HTTPError('url',code,'error',{},None))
        with self.assertRaises(urllib.error.HTTPError):
            self.run_detector({},urllib.error.HTTPError('url',404,'missing checksum',{},None))
    def test_force_skips_completeness_lookup(self):
        output,calls=self.run_detector(None,force=True)
        self.assertIn('pending=true',output)
        self.assertEqual(calls,1)
    def test_recipe_changes_and_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir();p=root/'config/bridge.conf'
            p.write_bytes(b'a=1\n');original=detect.recipe_fingerprint(root)
            p.write_bytes(b'a=1\r\n');self.assertEqual(original,detect.recipe_fingerprint(root))
            p.write_bytes(b'a=2\n');self.assertNotEqual(original,detect.recipe_fingerprint(root))
            (root/'scripts').mkdir();q=root/'scripts/build.ps1';q.write_text('build')
            self.assertNotEqual(original,detect.recipe_fingerprint(root))
if __name__=='__main__':unittest.main()
