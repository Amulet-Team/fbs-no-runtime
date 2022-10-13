from fbs import path, LOADED_PROFILES
from fbs.resources import _copy
from fbs._source import default_path
from fbs.paths import get_build_system_dir


def _generate_installer_resources():
    for path_fn in default_path, path:
        for profile in LOADED_PROFILES:
            _copy(path_fn, f"{get_build_system_dir()}/installer/" + profile, path("target/installer"))
