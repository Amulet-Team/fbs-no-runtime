from pbt.resources import copy_with_filtering
from pbt.paths import default_path, project_path
from os import makedirs, rename
from os.path import exists
from shutil import rmtree, copy
from subprocess import check_call, DEVNULL


def create_repo_fedora():
    if exists(project_path("target/repo")):
        rmtree(project_path("target/repo"))
    makedirs(project_path("target/repo/${version}"))
    copy(project_path("target/${installer}"), project_path("target/repo/${version}"))
    check_call(["createrepo_c", "."], cwd=(project_path("target/repo")), stdout=DEVNULL)
    repo_file = project_path("${build_system_dir}/repo/fedora/${app_name}.repo")
    use_default = not exists(repo_file)
    if use_default:
        repo_file = default_path("${build_system_dir}/repo/fedora/AppName.repo")
    copy_with_filtering(
        repo_file, project_path("target/repo"), files_to_filter=[repo_file]
    )
    if use_default:
        rename(
            project_path("target/repo/AppName.repo"),
            project_path("target/repo/${app_name}.repo"),
        )
