from pbt import SETTINGS
from pbt.paths import project_path
from pbt._gpg import preset_gpg_passphrase
from subprocess import check_call, DEVNULL


def sign_installer_arch():
    installer = project_path("target/${installer}")
    # Prevent GPG from prompting us for the passphrase when signing:
    preset_gpg_passphrase()
    check_call(
        [
            "gpg",
            "--batch",
            "--yes",
            "-u",
            SETTINGS["gpg_key"],
            "--output",
            installer + ".sig",
            "--detach-sig",
            installer,
        ],
        stdout=DEVNULL,
    )
