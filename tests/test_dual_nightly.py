import importlib.util, unittest
from pathlib import Path
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
