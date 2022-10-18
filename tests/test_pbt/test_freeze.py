from pbt.paths import project_path
from pbt.freeze import _generate_resources
from os.path import exists
from tests.test_pbt import PbtTest


class GenerateResourcesTest(PbtTest):
    def test_generate_resources(self):
        self.init_pbt("Mac")
        _generate_resources()
        info_plist = project_path("${freeze_dir}/Contents/Info.plist")
        self.assertTrue(exists(info_plist))
        with open(info_plist) as f:
            self.assertIn("MyApp", f.read(), "Did not replace '${app_name}' by 'MyApp'")
