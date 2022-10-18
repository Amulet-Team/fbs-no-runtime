from pbt import SETTINGS
from pbt.freeze import _generate_resources, run_pyinstaller
from pbt.resources import get_icons
from pbt.paths import project_path
from os import makedirs, unlink, rename, symlink
from os.path import exists
from shutil import copy, rmtree
from subprocess import run


def freeze_mac(debug=False):
    if not exists(project_path("target/Icon.icns")):
        _generate_iconset()
        run(["iconutil", "-c", "icns", project_path("target/Icon.iconset")], check=True)
    args = []
    if not (debug or SETTINGS["show_console_window"]):
        args.append("--windowed")
    args.extend(["--icon", project_path("target/Icon.icns")])
    bundle_identifier = SETTINGS["mac_bundle_identifier"]
    if bundle_identifier:
        args.extend(["--osx-bundle-identifier", bundle_identifier])
    run_pyinstaller(args, debug)
    _remove_unwanted_pyinstaller_files()
    _fix_sparkle_delta_updates()
    _generate_resources()


def _generate_iconset():
    makedirs(project_path("target/Icon.iconset"), exist_ok=True)
    for size, scale, icon_path in get_icons():
        dest_name = "icon_%dx%d" % (size, size)
        if scale != 1:
            dest_name += "@%dx" % scale
        dest_name += ".png"
        copy(icon_path, project_path("target/Icon.iconset/" + dest_name))


def _remove_unwanted_pyinstaller_files():
    for unwanted in ("include", "lib", "lib2to3"):
        try:
            unlink(project_path("${freeze_dir}/Contents/MacOS/" + unwanted))
        except FileNotFoundError:
            pass
        try:
            rmtree(project_path("${freeze_dir}/Contents/Resources/" + unwanted))
        except FileNotFoundError:
            pass


def _fix_sparkle_delta_updates():
    # Sparkle's Delta Updates mechanism does not support signed non-Mach-O files
    # in Contents/MacOS. base_library.zip, which is created by PyInstaller,
    # violates this. We therefore move base_library.zip to Contents/Resources.
    # Fortunately, everything still works if we then create a symlink
    # MacOS/base_library.zip -> ../Resources/base_library.zip.
    rename(
        project_path("${freeze_dir}/Contents/MacOS/base_library.zip"),
        project_path("${freeze_dir}/Contents/Resources/base_library.zip"),
    )
    symlink(
        "../Resources/base_library.zip",
        project_path("${freeze_dir}/Contents/MacOS/base_library.zip"),
    )
