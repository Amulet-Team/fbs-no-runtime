from pbt.error import PbtError

import os
import sys

PLATFORM_NAME = None
LINUX_DISTRIBUTION = None
APPLICATION_CONTEXT = None


def get():
    return PLATFORM_NAME, LINUX_DISTRIBUTION, APPLICATION_CONTEXT


def restore(platform_name, linux_distribution, application_context):
    global PLATFORM_NAME, LINUX_DISTRIBUTION, APPLICATION_CONTEXT
    PLATFORM_NAME = platform_name
    LINUX_DISTRIBUTION = linux_distribution
    APPLICATION_CONTEXT = application_context


def is_windows():
    """
    Return True if the current OS is Windows, False otherwise.
    """
    return name() == "Windows"


def is_mac():
    """
    Return True if the current OS is macOS, False otherwise.
    """
    return name() == "Mac"


def is_linux():
    """
    Return True if the current OS is Linux, False otherwise.
    """
    return name() == "Linux"


def name():
    """
    Returns 'Windows', 'Mac' or 'Linux', depending on the current OS. If the OS
    can't be determined, PbtError is raised.
    """
    global PLATFORM_NAME
    if PLATFORM_NAME is None:
        PLATFORM_NAME = _get_name()
    return PLATFORM_NAME


def _get_name():
    if sys.platform in ("win32", "cygwin"):
        return "Windows"
    if sys.platform == "darwin":
        return "Mac"
    if sys.platform.startswith("linux"):
        return "Linux"
    raise PbtError("Unknown operating system.")


def is_ubuntu():
    try:
        return linux_distribution() in ("Ubuntu", "Linux Mint", "Pop!_OS")
    except FileNotFoundError:
        return False


def is_arch_linux():
    try:
        return linux_distribution() in ("Arch Linux", "Manjaro Linux")
    except FileNotFoundError:
        return False


def is_fedora():
    try:
        return linux_distribution() in ("Fedora", "CentOS Linux")
    except FileNotFoundError:
        return False


def linux_distribution():
    global LINUX_DISTRIBUTION
    if LINUX_DISTRIBUTION is None:
        LINUX_DISTRIBUTION = _get_linux_distribution()
    return LINUX_DISTRIBUTION


def _get_linux_distribution():
    if not is_linux():
        return ""
    try:
        os_release = _get_os_release_name()
    except OSError:
        pass
    else:
        if os_release:
            return os_release
    return "<unknown>"


def is_gnome_based():
    curr_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    return curr_desktop in ("unity", "gnome", "x-cinnamon")


def is_kde_based():
    curr_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if curr_desktop == "kde":
        return True
    gdmsession = os.environ.get("GDMSESSION", "").lower()
    return gdmsession.startswith("kde")


def _get_os_release_name():
    with open("/etc/os-release", "r") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("NAME="):
                name = line[len("NAME=") :]
                return name.strip('"')
