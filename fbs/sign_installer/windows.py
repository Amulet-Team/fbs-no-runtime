from fbs import SETTINGS
from fbs.paths import project_path
from fbs.sign.windows import sign_file


def sign_installer_windows():
    installer = project_path("target/${installer}")
    sign_file(installer, SETTINGS["app_name"] + " Setup", SETTINGS["url"])
