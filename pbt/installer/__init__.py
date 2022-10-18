from pbt import LOADED_PROFILES
from pbt.resources import _copy
from pbt.paths import default_path, project_path


def _generate_installer_resources():
    for path_fn in default_path, project_path:
        for profile in LOADED_PROFILES:
            _copy(
                path_fn,
                "${build_system_dir}/installer/" + profile,
                project_path("target/installer"),
            )
