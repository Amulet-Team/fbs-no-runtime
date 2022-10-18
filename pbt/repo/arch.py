from pbt import SETTINGS
from pbt.error import PbtError
from pbt.paths import project_path
from pbt._variables import get_version
from os import makedirs
from os.path import exists, join
from shutil import rmtree, copy
from subprocess import check_call, DEVNULL


def create_repo_arch():
    if not exists(project_path("target/${installer}.sig")):
        raise PbtError(
            "Installer does not exist or is not signed. Maybe you need to "
            "run:\n"
            "    pbt signinst"
        )
    dest_dir = project_path("target/repo")
    if exists(dest_dir):
        rmtree(dest_dir)
    makedirs(dest_dir)
    app_name = SETTINGS["app_name"]
    pkg_file = project_path("target/${installer}")
    pkg_file_versioned = "%s-%s.pkg.tar.xz" % (app_name, get_version())
    copy(pkg_file, join(dest_dir, pkg_file_versioned))
    copy(pkg_file + ".sig", join(dest_dir, pkg_file_versioned + ".sig"))
    check_call(
        ["repo-add", "%s.db.tar.gz" % app_name, pkg_file_versioned],
        cwd=dest_dir,
        stdout=DEVNULL,
    )
    # Ensure the permissions are correct if uploading to a server:
    check_call(["chmod", "g-w", "-R", dest_dir])
