from pbt import SETTINGS
from pbt.installer import _generate_installer_resources
from pbt.resources import get_icons
from pbt.platform import is_arch_linux
from pbt.paths import project_path
from pbt._variables import get_version
from os import makedirs, remove, rename
from os.path import join, dirname, exists
from shutil import copy, rmtree, copytree
from subprocess import run, DEVNULL


def generate_installer_files():
    if exists(project_path("target/installer")):
        rmtree(project_path("target/installer"))
    copytree(
        project_path("${freeze_dir}"), project_path("target/installer/opt/${app_name}")
    )
    _generate_installer_resources()
    # Special handling of the .desktop file: Replace AppName by actual name.
    apps_dir = project_path("target/installer/usr/share/applications")
    rename(
        join(apps_dir, "AppName.desktop"),
        join(apps_dir, SETTINGS["app_name"] + ".desktop"),
    )
    _generate_icons()


def run_fpm(output_type):
    dest = project_path("target/${installer}")
    if exists(dest):
        remove(dest)
    # Lower-case the name to avoid the following fpm warning:
    #  > Debian tools (dpkg/apt) don't do well with packages that use capital
    #  > letters in the name. In some cases it will automatically downcase
    #  > them, in others it will not. It is confusing. Best to not use any
    #  > capital letters at all.
    name = SETTINGS["app_name"].lower()
    args = [
        "fpm",
        "-s",
        "dir",
        # We set the log level to error because fpm prints the following warning
        # even if we don't have anything in /etc:
        #  > Debian packaging tools generally labels all files in /etc as config
        #  > files, as mandated by policy, so fpm defaults to this behavior for
        #  > deb packages. You can disable this default behavior with
        #  > --deb-no-default-config-files flag
        "--log",
        "error",
        "-C",
        project_path("target/installer"),
        "-n",
        name,
        "-v",
        get_version(),
        "--vendor",
        SETTINGS["author"],
        "-t",
        output_type,
        "-p",
        dest,
    ]
    if SETTINGS["description"]:
        args.extend(["--description", SETTINGS["description"]])
    if SETTINGS["author_email"]:
        args.extend(["-m", "%s <%s>" % (SETTINGS["author"], SETTINGS["author_email"])])
    if SETTINGS["url"]:
        args.extend(["--url", SETTINGS["url"]])
    for dependency in SETTINGS["depends"]:
        args.extend(["-d", dependency])
    if is_arch_linux():
        for opt_dependency in SETTINGS["depends_opt"]:
            args.extend(["--pacman-optional-depends", opt_dependency])
    try:
        run(args, check=True, stdout=DEVNULL)
    except FileNotFoundError:
        raise FileNotFoundError(
            "pbt could not find executable 'fpm'. Please install fpm using the "
            "instructions at "
            "https://fpm.readthedocs.io/en/latest/installation.html."
        ) from None


def _generate_icons():
    dest_root = project_path("target/installer/usr/share/icons/hicolor")
    makedirs(dest_root)
    icons_fname = "%s.png" % SETTINGS["app_name"]
    for size, _, icon_path in get_icons():
        icon_dest = join(dest_root, "%dx%d" % (size, size), "apps", icons_fname)
        makedirs(dirname(icon_dest))
        copy(icon_path, icon_dest)
