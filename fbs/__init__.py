from fbs import _state
from fbs._state import LOADED_PROFILES
from fbs.error import FbsError
from fbs._fbs import get_core_settings, get_default_profiles
from fbs._settings import load_settings, expand_placeholders
from fbs.paths import (
    fix_path,
    get_settings_paths,
    get_configurable_settings,
    get_project_root,
    get_version,
)
from os.path import abspath

"""
fbs populates SETTINGS with the current build settings. A typical example is
SETTINGS['app_name'], which you define in build_system/build/settings/base.json.
"""
SETTINGS = _state.SETTINGS


def init(project_dir):
    """
    Call this if you are invoking neither `fbs` on the command line nor
    fbs.cmdline.main() from Python.
    """
    SETTINGS.update(get_core_settings(abspath(project_dir)))
    SETTINGS.update(get_configurable_settings())
    for profile in get_default_profiles():
        activate_profile(profile)
    get_version()


def activate_profile(profile_name):
    """
    By default, fbs only loads some settings. For instance,
    build_system/build/settings/base.json and .../`os`.json where `os` is one of "mac",
    "linux" or "windows". This function lets you load other settings on the fly.
    A common example would be during a release, where release.json contains the
    production server URL instead of a staging server.
    """
    LOADED_PROFILES.append(profile_name)
    json_paths = get_settings_paths(LOADED_PROFILES)
    project_dir = get_project_root()
    core_settings = get_core_settings(project_dir)
    SETTINGS.update(load_settings(json_paths, core_settings))
