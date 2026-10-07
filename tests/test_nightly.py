import importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('detect',Path(__file__).parents[1]/'scripts/detect-nightly.py')
detect=importlib.util.module_from_spec(spec);spec.loader.exec_module(detect)
class NightlyTests(unittest.TestCase):
    def test_version_sequence(self):
        self.assertEqual(detect.version_from_distance("1.0",1),"1.0")
        self.assertEqual(detect.version_from_distance("1.0",2),"1.1")
        self.assertEqual(detect.version_from_distance("1.0",12),"1.11")
    def test_complete_pair(self):
        name='YR-MO-DXVK64-Bridge-vtest.zip'
        release={'draft':False,'assets':[{'name':name,'size':3},{'name':name+'.sha256','size':70}]}
        self.assertTrue(detect.release_complete(release,'test'))
        release['assets'].pop();self.assertFalse(detect.release_complete(release,'test'))
    def test_unrelated_and_empty_assets(self):
        self.assertFalse(detect.release_complete({'draft':False,'assets':[{'name':'other.zip','size':3}]},'test'))
        self.assertFalse(detect.release_complete({'draft':False,'assets':[]},'test'))
    def test_recipe_changes_and_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir();p=root/'config/bridge.conf'
            p.write_bytes(b'a=1\n');original=detect.recipe_fingerprint(root)
            p.write_bytes(b'a=1\r\n');self.assertEqual(original,detect.recipe_fingerprint(root))
            p.write_bytes(b'a=2\n');self.assertNotEqual(original,detect.recipe_fingerprint(root))
            (root/'scripts').mkdir();q=root/'scripts/build.ps1';q.write_text('build')
            self.assertNotEqual(original,detect.recipe_fingerprint(root))
if __name__=='__main__':unittest.main()
