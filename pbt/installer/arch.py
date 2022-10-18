from pbt.paths import project_path
from pbt.installer.linux import generate_installer_files, run_fpm
from subprocess import run


def create_installer_arch():
    generate_installer_files()
    # Avoid pacman warning "directory permissions differ" when installing:
    run(["chmod", "g-w", "-R", project_path("target/installer")], check=True)
    run_fpm("pacman")
