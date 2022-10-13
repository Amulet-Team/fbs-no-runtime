import os
import json
from os.path import join, normpath, dirname, exists

from fbs._state import SETTINGS
from functools import lru_cache
from fbs.error import FbsError
from fbs._settings import expand_placeholders


@lru_cache
def _get_paths() -> dict:
    """Get the user configurable paths mapping."""
    paths_file = project_path("paths.json")
    if os.path.isfile(paths_file):
        try:
            with open(paths_file) as f:
                _paths = json.load(f)
            if not isinstance(_paths, dict):
                raise TypeError("paths.json file must contain a dictionary if defined.")
        except Exception as e:
            raise FbsError(e) from e
        return _paths
    else:
        return {}


BuildSystemDefault = "build_system"
IconsDefault = "icons"


@lru_cache
def get_build_system_dir() -> str:
    """
    Get path to the build system directory in the project.
    Defaults to "build_system"
    """
    return _get_paths().get("build_path", BuildSystemDefault)


@lru_cache
def get_icon_dir() -> str:
    """
    Get the path to the icon directory in the project.
    Defaults to "icons"
    """
    return _get_paths().get("icons_path", "icons")


@lru_cache
def get_script_path() -> str:
    raise NotImplementedError


@lru_cache
def get_python_working_directory() -> str:
    return _get_paths().get("python_working_directory", "src")


def fix_path(base_dir, path_str):
    return normpath(join(base_dir, *path_str.split("/")))


def default_path(path_str: str) -> str:
    """
    Get the full path to a default file.
    Does not apply substitutions.
    >>> path = default_path("${build_system_dir}/build/settings/base.json")
    """
    defaults_dir = join(dirname(__file__), "_defaults")
    return fix_path(defaults_dir, path_str)


def project_path(path_str):
    """
    Return the absolute path of the given file in the project directory. For
    instance: path('src/my_app'). The `path_str` argument should always use
    forward slashes `/`, even on Windows. You can use placeholders to refer to
    settings. For example: path('${freeze_dir}/foo').
    """
    path_str = expand_placeholders(path_str, SETTINGS)
    try:
        project_dir = SETTINGS["project_dir"]
    except KeyError:
        error_message = "Cannot call path(...) until fbs.init(...) has been " "called."
        raise FbsError(error_message) from None
    return fix_path(project_dir, path_str)


def get_settings_paths(project_dir, profiles):
    return list(
        filter(
            exists,
            (
                path_fn("{$build_system_dir}/build/settings/%s.json" % profile)
                for path_fn in (default_path, lambda p: fix_path(project_dir, p))
                for profile in profiles
            ),
        )
    )
