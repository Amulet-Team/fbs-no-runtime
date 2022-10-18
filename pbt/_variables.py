from multiprocessing import Array, Process
from ctypes import c_char
from pbt._state import SETTINGS
from pbt.error import PbtError
from pbt._util import _get_attr
from pbt.paths import project_path, get_python_path
from packaging.version import Version, InvalidVersion


def resolve_variables():
    get_version()


def get_version() -> str:
    """Get the module version"""
    if SETTINGS["version"].startswith("attr:"):
        # try and get the version number from module.__version__
        attr_path = SETTINGS["version"][5:].lstrip()
        module_name, attr_name = attr_path.rsplit(".", 1)
        if not module_name or not attr_name:
            raise PbtError(
                "attr: format must define a path to a variable. Eg my_app.__version__"
            )
        attr = Array(c_char, b"\x00" * 2**15)
        p = Process(
            target=_get_attr,
            args=(
                module_name,
                attr_name,
                attr,
                project_path(get_python_path()),
            ),
        )
        p.start()
        p.join()
        set_version(attr[:].decode().strip("\x00"))
    if "major" not in SETTINGS:
        # initialise major, minor and patch
        set_version(SETTINGS["version"])
    return SETTINGS["version"]


def set_version(version_string: str):
    try:
        parsed_version = Version(version_string)
    except InvalidVersion:
        raise PbtError(
            f"Version must be a PEP 440 compatible version number string. Got {version_string}"
        )
    else:
        SETTINGS["version"] = version_string
        SETTINGS["major"] = parsed_version.major
        SETTINGS["minor"] = parsed_version.minor
        SETTINGS["patch"] = parsed_version.micro
