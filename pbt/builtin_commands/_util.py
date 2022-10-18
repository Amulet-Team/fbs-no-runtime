from collections import OrderedDict
from pbt.error import PbtError
from pbt.paths import get_build_system_dir, project_path
from getpass import getpass
from os.path import exists
from pathlib import Path
from packaging.version import Version, InvalidVersion

import json
import re

BASE_JSON = "${build_system_dir}/build/settings/base.json"
SECRET_JSON = "${build_system_dir}/build/settings/secret.json"


def prompt_for_value(value, optional=False, default="", password=False, choices=()):
    message = value
    if choices:
        choices_dict = OrderedDict((str(i + 1), c) for (i, c) in enumerate(choices))
        message += ": "
        message += " or ".join("%s) %s" % tpl for tpl in choices_dict.items())
    if default:
        message += " [%s] " % (choices.index(default) + 1 if choices else default)
    message += ": "
    prompt = getpass if password else input
    result = prompt(message).strip()
    if not result and default:
        print(default)
        return default
    if not optional:
        while not result or (choices and result not in choices_dict):
            result = prompt(message).strip()
    return choices_dict[result] if choices else result


def require_existing_project():
    if not (
        exists(project_path(get_build_system_dir()))
        and exists(project_path("${build_system_dir}/icons"))
    ):
        raise PbtError(
            f"Could not find {get_build_system_dir()} directory. Are you in the right folder?\n"
            "If yes, did you already run\n"
            "    pbt startproject ?"
        )


def require_frozen_app():
    if not exists(project_path("${freeze_dir}")):
        raise PbtError(
            "It seems your app has not yet been frozen. Please run:\n" "    pbt freeze"
        )


def require_installer():
    installer = project_path("target/${installer}")
    if not exists(installer):
        raise PbtError(
            "Installer does not exist. Maybe you need to run:\n" "    pbt installer"
        )


def update_json(f_path, dict_):
    f = Path(f_path)
    try:
        contents = f.read_text()
    except FileNotFoundError:
        indent = _infer_indent(Path(project_path(BASE_JSON)).read_text())
        new_contents = json.dumps(dict_, indent=indent)
    else:
        new_contents = _update_json_str(contents, dict_)
    f.write_text(new_contents)


def is_valid_version(version_str):
    try:
        Version(version_str)
    except InvalidVersion:
        return False
    else:
        return True


def _update_json_str(json_str, dict_):
    if not dict_:
        return json_str
    data = json.loads(json_str, object_pairs_hook=OrderedDict)
    data.update(dict_)
    indent = _infer_indent(json_str)
    return json.dumps(data, indent=indent)


def _infer_indent(json_str):
    start = json_str.find("{")
    if start == -1:
        return None
    match = re.search("\n(\\s+)", json_str[start:])
    return match.group(1) if match else None
