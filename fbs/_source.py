"""
This module contains functions that should only be called by module `fbs`, or
when running from source.
"""

from os.path import join, normpath, dirname, exists


def get_settings_paths(project_dir, profiles):
    return list(
        filter(
            exists,
            (
                path_fn("src/build/settings/%s.json" % profile)
                for path_fn in (default_path, lambda p: path(project_dir, p))
                for profile in profiles
            ),
        )
    )


def default_path(path_str):
    defaults_dir = join(dirname(__file__), "_defaults")
    return path(defaults_dir, path_str)


def path(base_dir, path_str):
    return normpath(join(base_dir, *path_str.split("/")))
