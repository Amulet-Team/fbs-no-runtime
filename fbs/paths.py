import os
import json
from functools import lru_cache
from fbs import path
from fbs.error import FbsError


@lru_cache
def _get_paths() -> dict:
    paths_file = path("paths.json")
    if os.path.isfile(paths_file):
        try:
            with open(paths_file) as f:
                _paths = json.load(f)
            if not isinstance(_paths, dict):
                raise TypeError("paths.json file must contain a dictionary if defined.")
        except Exception as e:
            raise FbsError(e) from e
    return _paths


BuildPipelineDefault = "build_pipeline"
IconsDefault = "icons"


@lru_cache
def get_build_path():
    return _get_paths().get("build_path", BuildPipelineDefault)


@lru_cache
def get_icon_path():
    return _get_paths().get("icons_path", "icons")


@lru_cache
def get_script_path():
    raise NotImplementedError


@lru_cache
def get_python_working_directory():
    return _get_paths().get("python_working_directory", "src")
