from pbt import SETTINGS
from pbt._state import LOADED_PROFILES
from pbt.resources import _copy
from pbt.platform import is_mac
from pbt.paths import default_path, project_path, get_script_path
from os import rename
from pathlib import PurePath
from subprocess import run


def run_pyinstaller(extra_args=None, debug=False):
    if extra_args is None:
        extra_args = []
    app_name = SETTINGS["app_name"]
    # Would like log level WARN when not debugging. This works fine for
    # PyInstaller 3.3. However, for 3.4, it gives confusing warnings
    # "hidden import not found". So use ERROR instead.
    log_level = "DEBUG" if debug else "ERROR"
    args = [
        "pyinstaller",
        "--name",
        app_name,
        "--noupx",
        "--log-level",
        log_level,
        "--noconfirm",
    ]
    for hidden_import in SETTINGS["hidden_imports"]:
        args.extend(["--hidden-import", hidden_import])
    args.extend(SETTINGS.get("extra_pyinstaller_args", []))
    args.extend(extra_args)
    args.extend(
        [
            "--distpath",
            project_path("target"),
            "--specpath",
            project_path("target/PyInstaller"),
            "--workpath",
            project_path("target/PyInstaller"),
        ]
    )
    if debug:
        args.extend(["--debug", "all"])
        if is_mac():
            # Force generation of an .app bundle. Otherwise, PyInstaller skips
            # it when --debug is given.
            args.append("-w")
    args.append(get_script_path()[0])
    run(args, check=True)
    output_dir = project_path("target/" + app_name + (".app" if is_mac() else ""))
    freeze_dir = project_path("${freeze_dir}")
    # In most cases, rename(src, dst) silently "works" when src == dst. But on
    # some Windows drives, it raises a FileExistsError. So check src != dst:
    if PurePath(output_dir) != PurePath(freeze_dir):
        rename(output_dir, freeze_dir)


def _generate_resources():
    """
    Copy the data files from ${build_system_dir}/freeze to ${freeze_dir}.
    Automatically filters files mentioned in the setting files_to_filter:
    Placeholders such as ${app_name} are automatically replaced by the
    corresponding setting in files on that list.
    """
    freeze_dir = project_path("${freeze_dir}")
    for path_fn in default_path, project_path:
        for profile in LOADED_PROFILES:
            _copy(path_fn, "${build_system_dir}/freeze/" + profile, freeze_dir)
