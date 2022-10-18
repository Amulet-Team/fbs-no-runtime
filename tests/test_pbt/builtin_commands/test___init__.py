from pbt.paths import project_path
from pbt.builtin_commands import freeze, installer
from pbt.platform import is_mac, is_windows, is_linux
from os import listdir
from os.path import exists, join
from tests.test_pbt import PbtTest


class BuiltInCommandsTest(PbtTest):
    def test_freeze_installer(self):
        freeze()
        if is_mac():
            executable = project_path("${freeze_dir}/Contents/MacOS/${app_name}")
        elif is_windows():
            executable = project_path("${freeze_dir}/${app_name}.exe")
        else:
            executable = project_path("${freeze_dir}/${app_name}")
        self.assertTrue(exists(executable), executable + " does not exist")
        installer()
        self.assertTrue(exists(project_path("target/${installer}")))
        if is_linux():
            applications_dir = project_path("target/installer/usr/share/applications")
            self.assertEqual(["MyApp.desktop"], listdir(applications_dir))
            with open(join(applications_dir, "MyApp.desktop")) as f:
                self.assertIn("MyApp", f.read())

    def setUp(self):
        super().setUp()
        self.init_pbt()
