"""
This module contains all of pbt's built-in commands. They are invoked when you
run `pbt <command>` on the command line. But you are also free to import them in
your Python build script and execute them there.
"""
from pbt import SETTINGS, activate_profile
from pbt.builtin_commands._util import (
    prompt_for_value,
    is_valid_version,
    require_existing_project,
    update_json,
    require_frozen_app,
    require_installer,
)
from pbt.cmdline import command
from pbt.resources import copy_with_filtering
from pbt.upload import _upload_repo
from pbt.error import PbtError
from pbt.platform import (
    is_windows,
    is_mac,
    is_linux,
    is_arch_linux,
    is_ubuntu,
    is_fedora,
)
from pbt.paths import (
    BuildSystemDefault,
    get_script_path,
    get_python_path,
    get_build_system_dir,
    project_path,
    get_project_root,
)
from pbt._variables import get_version, set_version
from getpass import getuser
from importlib.util import find_spec
from os import listdir, remove, unlink, mkdir
from os.path import join, isfile, isdir, islink, dirname, exists, relpath
from shutil import rmtree
from unittest import TestSuite, TextTestRunner, defaultTestLoader

import logging
import os
import subprocess
import sys

_LOG = logging.getLogger(__name__)


@command
def startproject():
    """
    Start a new project in the current directory
    """
    if (
        exists(BuildSystemDefault)
        or exists("pyproject.toml")
        or exists("setup.cfg")
        or exists("src")
    ):
        raise PbtError(
            f"The src or {BuildSystemDefault} directory already exists. Aborting."
        )
    app = prompt_for_value("App name", default="MyApp")
    package_name = prompt_for_value("Package name", default="my_app")
    user = getuser().title()
    author = prompt_for_value("Author", default=user)
    eg_bundle_id = "com.%s.%s" % (
        author.lower().split()[0],
        "".join(app.lower().split()),
    )
    mac_bundle_identifier = prompt_for_value(
        "Mac bundle identifier (eg. %s, optional)" % eg_bundle_id, optional=True
    )
    mkdir("src")
    template_dir = join(dirname(__file__), "project_template")
    template_path = lambda relpath: join(template_dir, *relpath.split("/"))
    copy_with_filtering(
        template_dir,
        ".",
        {
            "app_name": app,
            "package_name": package_name,
            "author": author,
            "mac_bundle_identifier": mac_bundle_identifier,
        },
        files_to_filter=[
            template_path(f"{BuildSystemDefault}/build/settings/base.json"),
            template_path(f"{BuildSystemDefault}/build/settings/mac.json"),
            template_path("setup.cfg"),
            template_path("src/${package_name}"),
        ],
    )
    print("")
    _LOG.info(
        f"Created the src and {BuildSystemDefault} directories. You can now do:\n\n    pbt run"
    )


@command
def run():
    """
    Run your app from source
    """
    require_existing_project()
    env = dict(os.environ)
    path, extend = get_script_path()
    if extend:
        pythonpath = project_path(get_python_path())
        old_pythonpath = env.get("PYTHONPATH", "")
        if old_pythonpath:
            pythonpath += os.pathsep + old_pythonpath
        env["PYTHONPATH"] = pythonpath
    subprocess.run([sys.executable, path], env=env)


@command
def freeze(debug=False):
    """
    Compile your code to a standalone executable
    """
    require_existing_project()
    if not _has_module("PyInstaller"):
        raise PbtError(
            "Could not find PyInstaller. Maybe you need to:\n"
            "    pip install PyInstaller"
        )
    version = get_version()
    if not is_valid_version(version):
        raise PbtError(
            "Invalid version detected. It must be a PEP 440 compatible version number\n"
            f'such as "1.2.3" or an attribute path such as "attr: my_app.__version__". You have:\n\t"{version}".\n'
            f"Usually, this can be fixed in {get_build_system_dir()}/build/settings/base.json."
        )
    # Import respective functions late to avoid circular import
    # pbt <-> pbt.freeze.X.
    app_name = SETTINGS["app_name"]
    if is_mac():
        from pbt.freeze.mac import freeze_mac

        freeze_mac(debug=debug)
        executable = "target/%s.app/Contents/MacOS/%s" % (app_name, app_name)
    else:
        executable = join("target", app_name, app_name)
        if is_windows():
            from pbt.freeze.windows import freeze_windows

            freeze_windows(debug=debug)
            executable += ".exe"
        elif is_linux():
            if is_ubuntu():
                from pbt.freeze.ubuntu import freeze_ubuntu

                freeze_ubuntu(debug=debug)
            elif is_arch_linux():
                from pbt.freeze.arch import freeze_arch

                freeze_arch(debug=debug)
            elif is_fedora():
                from pbt.freeze.fedora import freeze_fedora

                freeze_fedora(debug=debug)
            else:
                from pbt.freeze.linux import freeze_linux

                freeze_linux(debug=debug)
        else:
            raise PbtError("Unsupported OS")
    _LOG.info(
        "Done. You can now run `%s`. If that doesn't work, see "
        "https://build-system.fman.io/troubleshooting.",
        executable,
    )


@command
def sign():
    """
    Sign your app, so the user's OS trusts it
    """
    require_frozen_app()
    if is_windows():
        from pbt.sign.windows import sign_windows

        sign_windows()
        _LOG.info(
            "Signed all binary files in %s and its subdirectories.",
            relpath(project_path("${freeze_dir}"), project_path(".")),
        )
    elif is_mac():
        _LOG.info("pbt does not yet implement `sign` on macOS.")
    else:
        _LOG.info("This platform does not support signing frozen apps.")


@command
def installer():
    """
    Create an installer for your app
    """
    require_frozen_app()
    linux_distribution_not_supported_msg = (
        "Your Linux distribution is not supported, sorry. "
        "You can run `pbt buildvm` followed by `pbt runvm` to start a Docker "
        "VM of a supported distribution."
    )
    try:
        installer_fname = SETTINGS["installer"]
    except KeyError:
        if is_linux():
            raise PbtError(linux_distribution_not_supported_msg)
        raise
    out_file = join("target", installer_fname)
    msg_parts = ["Created %s." % out_file]
    if is_windows():
        from pbt.installer.windows import create_installer_windows

        create_installer_windows()
    elif is_mac():
        from pbt.installer.mac import create_installer_mac

        create_installer_mac()
    elif is_linux():
        app_name = SETTINGS["app_name"]
        if is_ubuntu():
            from pbt.installer.ubuntu import create_installer_ubuntu

            create_installer_ubuntu()
            install_cmd = "sudo dpkg -i " + out_file
            remove_cmd = "sudo dpkg --purge " + app_name
        elif is_arch_linux():
            from pbt.installer.arch import create_installer_arch

            create_installer_arch()
            install_cmd = "sudo pacman -U " + out_file
            remove_cmd = "sudo pacman -R " + app_name
        elif is_fedora():
            from pbt.installer.fedora import create_installer_fedora

            create_installer_fedora()
            install_cmd = "sudo dnf install " + out_file
            remove_cmd = "sudo dnf remove " + app_name
        else:
            raise PbtError(linux_distribution_not_supported_msg)
        msg_parts.append(
            "You can for instance install it via the following command:\n"
            "    %s\n"
            "This places it in /opt/%s. To uninstall it again, you can use:\n"
            "    %s" % (install_cmd, app_name, remove_cmd)
        )
    else:
        raise PbtError("Unsupported OS")
    _LOG.info(" ".join(msg_parts))


@command
def sign_installer():
    """
    Sign installer, so the user's OS trusts it
    """
    if is_mac():
        _LOG.info("pbt does not yet implement `sign_installer` on macOS.")
        return
    if is_ubuntu():
        _LOG.info("Ubuntu does not support signing installers.")
        return
    require_installer()
    if is_windows():
        from pbt.sign_installer.windows import sign_installer_windows

        sign_installer_windows()
    elif is_arch_linux():
        from pbt.sign_installer.arch import sign_installer_arch

        sign_installer_arch()
    elif is_fedora():
        from pbt.sign_installer.fedora import sign_installer_fedora

        sign_installer_fedora()
    _LOG.info("Signed %s.", join("target", SETTINGS["installer"]))


@command
def repo():
    """
    Generate files for automatic updates
    """
    require_existing_project()
    if not _repo_is_supported():
        raise PbtError("This command is not supported on this platform.")
    app_name = SETTINGS["app_name"]
    pkg_name = app_name.lower()
    try:
        gpg_key = SETTINGS["gpg_key"]
    except KeyError:
        raise PbtError(
            "GPG key for code signing is not configured. You might want to "
            "either\n"
            "    1) run `pbt gengpgkey` or\n"
            f'    2) set "gpg_key" and "gpg_pass" in {get_build_system_dir()}/build/settings/.'
        )
    if is_ubuntu():
        from pbt.repo.ubuntu import create_repo_ubuntu

        if not SETTINGS["description"]:
            _LOG.info(
                'Hint: Your app\'s "description" is empty. Consider setting it '
                f"in {get_build_system_dir()}/build/settings/linux.json."
            )
        create_repo_ubuntu()
        _LOG.info(
            "Done. You can test the repository with the following commands:\n"
            '    echo "deb [arch=amd64] file://%s stable main" '
            "| sudo tee /etc/apt/sources.list.d/%s.list\n"
            "    sudo apt-key add %s\n"
            "    sudo apt-get update\n"
            "    sudo apt-get install %s\n"
            "To revert these changes:\n"
            "    sudo dpkg --purge %s\n"
            "    sudo apt-key del %s\n"
            "    sudo rm /etc/apt/sources.list.d/%s.list\n"
            "    sudo apt-get update",
            project_path("target/repo"),
            pkg_name,
            project_path("${build_system_dir}/sign/linux/public-key.gpg"),
            pkg_name,
            pkg_name,
            gpg_key,
            pkg_name,
            extra={"wrap": False},
        )
    elif is_arch_linux():
        from pbt.repo.arch import create_repo_arch

        create_repo_arch()
        _LOG.info(
            "Done. You can test the repository with the following commands:\n"
            "    sudo cp /etc/pacman.conf /etc/pacman.conf.bu\n"
            "    echo -e '\\n[%s]\\nServer = file://%s' "
            "| sudo tee -a /etc/pacman.conf\n"
            "    sudo pacman-key --add %s\n"
            "    sudo pacman-key --lsign-key %s\n"
            "    sudo pacman -Syu %s\n"
            "To revert these changes:\n"
            "    sudo pacman -R %s\n"
            "    sudo pacman-key --delete %s\n"
            "    sudo mv /etc/pacman.conf.bu /etc/pacman.conf",
            app_name,
            project_path("target/repo"),
            project_path("${build_system_dir}/sign/linux/public-key.gpg"),
            gpg_key,
            pkg_name,
            pkg_name,
            gpg_key,
            extra={"wrap": False},
        )
    else:
        assert is_fedora()
        from pbt.repo.fedora import create_repo_fedora

        create_repo_fedora()
        _LOG.info(
            "Done. You can test the repository with the following commands:\n"
            "    sudo rpm -v --import %s\n"
            "    sudo dnf config-manager --add-repo file://%s/target/repo\n"
            "    sudo dnf install %s\n"
            "To revert these changes:\n"
            "    sudo dnf remove %s\n"
            "    sudo rm /etc/yum.repos.d/*%s*.repo\n"
            "    sudo rpm --erase gpg-pubkey-%s",
            project_path("${build_system_dir}/sign/linux/public-key.gpg"),
            get_project_root(),
            pkg_name,
            pkg_name,
            app_name,
            gpg_key[-8:].lower(),
            extra={"wrap": False},
        )


def _repo_is_supported():
    return is_ubuntu() or is_arch_linux() or is_fedora()


@command
def upload():
    """
    Upload installer and repository to pbt.sh
    """
    require_existing_project()
    try:
        username = SETTINGS["fbs_user"]
        password = SETTINGS["fbs_pass"]
    except KeyError as e:
        raise PbtError(
            'Could not find setting "%s". You may want to invoke one of the '
            "following:\n"
            " * pbt register\n"
            " * pbt login" % (e.args[0],)
        ) from None
    _upload_repo(username, password)
    app_name = SETTINGS["app_name"]
    url = lambda p: "https://fbs.sh/%s/%s/%s" % (username, app_name, p)
    message = "Done! "
    pkg_name = app_name.lower()
    installer_url = url(SETTINGS["installer"])
    if is_linux():
        message += (
            "Your users can now install your app via the following " "commands:\n"
        )
        format_commands = lambda *cmds: "\n".join("    " + c for c in cmds)
        repo_url = url(SETTINGS["repo_subdir"])
        if is_ubuntu():
            message += format_commands(
                "sudo apt-get install apt-transport-https",
                "wget -qO - %s | sudo apt-key add -" % url("public-key.gpg"),
                "echo 'deb [arch=amd64] %s stable main' | " % repo_url
                + "sudo tee /etc/apt/sources.list.d/%s.list" % pkg_name,
                "sudo apt-get update",
                "sudo apt-get install " + pkg_name,
            )
            message += (
                "\nIf they already have your app installed, they can "
                "force an immediate update via:\n"
            )
            message += format_commands(
                "sudo apt-get update "
                '-o Dir::Etc::sourcelist="/etc/apt/sources.list.d/%s.list" '
                '-o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0"' % pkg_name,
                "sudo apt-get install --only-upgrade " + pkg_name,
            )
        elif is_arch_linux():
            message += format_commands(
                "curl -O %s && " % url("public-key.gpg")
                + "sudo pacman-key --add public-key.gpg && "
                + "sudo pacman-key --lsign-key %s && " % SETTINGS["gpg_key"]
                + "rm public-key.gpg",
                "echo -e '\\n[%s]\\nServer = %s' | sudo tee -a /etc/pacman.conf"
                % (app_name, repo_url),
                "sudo pacman -Syu " + pkg_name,
            )
            message += (
                "\nIf they already have your app installed, they can "
                "force an immediate update via:\n"
            )
            message += format_commands("sudo pacman -Syu --needed " + pkg_name)
        elif is_fedora():
            message += format_commands(
                "sudo rpm -v --import " + url("public-key.gpg"),
                "sudo dnf config-manager --add-repo %s/%s.repo" % (repo_url, app_name),
                "sudo dnf install " + pkg_name,
            )
            message += (
                "\n(On CentOS, replace 'dnf' by 'yum' and "
                "'dnf config-manager' by 'yum-config-manager'.)"
            )
            message += (
                "\nIf they already have your app installed, they can "
                "force an immediate update via:\n"
            )
            message += format_commands("sudo dnf upgrade %s --refresh" % pkg_name)
            message += "\nThis is for Fedora. For CentOS, use:\n"
            message += format_commands(
                "sudo yum clean all && sudo yum upgrade " + pkg_name
            )
        else:
            raise PbtError("This Linux distribution is not supported.")
        message += (
            "\nFinally, your users can also install without automatic "
            "updates by downloading:\n    " + installer_url
        )
        extra = {"wrap": False}
    else:
        message += "Your users can now download and install %s." % installer_url
        extra = None
    _LOG.info(message, extra=extra)


@command
def release(version=None):
    """
    Bump version and run clean,freeze,...,upload
    """
    require_existing_project()
    if version is None:
        curr_version = get_version()
        next_version = _get_next_version(curr_version)
        release_version = prompt_for_value("Release version", default=next_version)
    elif version == "current":
        release_version = get_version()
    else:
        release_version = version
    if not is_valid_version(release_version):
        if not is_valid_version(version):
            raise PbtError(
                "The release version of your app is invalid. It must be a PEP 440 compatible version number\n"
                f'such as "1.2.3" or an attribute path such as "attr: my_app.__version__". You have:\n\t"{version}".\n'
                f"Usually, this can be fixed in {get_build_system_dir()}/build/settings/base.json."
            )
    activate_profile("release")
    set_version(release_version)
    log_level = _LOG.level
    if log_level == logging.NOTSET:
        _LOG.setLevel(logging.WARNING)
    try:
        clean()
        freeze()
        if is_windows() and _has_windows_codesigning_certificate():
            sign()
        installer()
        if (
            (is_windows() and _has_windows_codesigning_certificate())
            or is_arch_linux()
            or is_fedora()
        ):
            sign_installer()
        if _repo_is_supported():
            repo()
    finally:
        _LOG.setLevel(log_level)
    upload()
    base_json = "${build_system_dir}/build/settings/base.json"
    update_json(project_path(base_json), {"version": release_version})
    _LOG.info("Also, %s was updated with the new version.", base_json)


@command
def test():
    """
    Execute your automated tests
    """
    require_existing_project()
    sys.path.append(project_path(get_python_path()))
    suite = TestSuite()
    test_dirs = SETTINGS["test_dirs"]
    for test_dir in map(project_path, test_dirs):
        sys.path.append(test_dir)
        try:
            dir_names = listdir(test_dir)
        except FileNotFoundError:
            continue
        for dir_name in dir_names:
            dir_path = join(test_dir, dir_name)
            if isfile(join(dir_path, "__init__.py")):
                suite.addTest(
                    defaultTestLoader.discover(dir_name, top_level_dir=test_dir)
                )
    has_tests = bool(list(suite))
    if has_tests:
        TextTestRunner().run(suite)
    else:
        _LOG.warning(
            "No tests found. You can add them to:\n * " + "\n * ".join(test_dirs)
        )


@command
def clean():
    """
    Remove previous build outputs
    """
    try:
        rmtree(project_path("target"))
    except FileNotFoundError:
        return
    except OSError:
        # In a docker container, target/ may be mounted so we can't delete it.
        # Delete its contents instead:
        for f in listdir(project_path("target")):
            fpath = join(project_path("target"), f)
            if isdir(fpath):
                rmtree(fpath, ignore_errors=True)
            elif isfile(fpath):
                remove(fpath)
            elif islink(fpath):
                unlink(fpath)


def _has_windows_codesigning_certificate():
    assert is_windows()
    from pbt.sign.windows import _CERTIFICATE_PATH

    return exists(project_path(_CERTIFICATE_PATH))


def _has_module(name):
    return bool(find_spec(name))


def _get_next_version(version):
    version_parts = version.split(".")
    next_patch = str(int(version_parts[-1]) + 1)
    return ".".join(version_parts[:-1]) + "." + next_patch
