from pbt.paths import project_path
from pbt._gpg import preset_gpg_passphrase
from subprocess import check_call, DEVNULL


def sign_installer_fedora():
    # Prevent GPG from prompting us for the passphrase when signing:
    preset_gpg_passphrase()
    check_call(
        ["rpm", "--addsign", project_path("target/${installer}")], stdout=DEVNULL
    )
