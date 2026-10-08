import contextlib, importlib.util, os, tempfile, unittest, urllib.error
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('dual',Path(__file__).parents[1]/'scripts/detect-dual-nightly.py')
dual=importlib.util.module_from_spec(spec);spec.loader.exec_module(dual)
class DualNightlyTests(unittest.TestCase):
    def test_either_upstream_change_creates_new_tag(self):
        a,b,c='a'*40,'b'*40,'c'*40
        original=dual.nightly_tag('1.1',a,b,'recipe')
        self.assertNotEqual(original,dual.nightly_tag('1.1',c,b,'recipe'))
        self.assertNotEqual(original,dual.nightly_tag('1.1',a,c,'recipe'))
        self.assertNotEqual(original,dual.nightly_tag('1.1',a,b,'new-recipe'))
        self.assertEqual(original,dual.nightly_tag('1.1',a,b,'recipe'))
    def test_mutable_or_malformed_refs_rejected(self):
        for ref in ('main','short','z'*40):
            with self.assertRaises(ValueError):dual.nightly_tag('1.1',ref,'a'*40,'recipe')
    def run_detector(self, lookup, completeness=True):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            output=Path(directory)/'output'
            environment={'GH_TOKEN':'test','GITHUB_REPOSITORY':'owner/repo',
                         'GITHUB_OUTPUT':str(output),'FORCE_REBUILD':'false'}
            responses=[{'sha':'a'*40},{'default_branch':'main','html_url':'https://github.com/owner/backend'},
                       {'sha':'b'*40},lookup]
            with patch.dict(os.environ,environment), patch.object(dual.detector,'source_version',return_value='1.2.3'), \
                 patch.object(dual.detector,'recipe_fingerprint',return_value='recipe'), \
                 patch.object(dual.detector,'api',side_effect=responses), \
                 patch.object(dual.detector,'release_complete',side_effect=completeness if isinstance(completeness,Exception) else None,
                              return_value=completeness):
                dual.main()
                return output.read_text()
    def test_missing_release_or_incomplete_pair_is_pending(self):
        missing=urllib.error.HTTPError('url',404,'missing',{},None)
        self.assertIn('pending=true',self.run_detector(missing))
        self.assertIn('pending=true',self.run_detector({},False))
        self.assertIn('pending=false',self.run_detector({},True))
    def test_lookup_network_errors_and_checksum_404_do_not_trigger_build(self):
        for code in (403,429,500):
            with self.subTest(code=code),self.assertRaises(urllib.error.HTTPError):
                self.run_detector(urllib.error.HTTPError('url',code,'error',{},None))
        with self.assertRaises(urllib.error.HTTPError):
            self.run_detector({},urllib.error.HTTPError('url',404,'missing checksum',{},None))
