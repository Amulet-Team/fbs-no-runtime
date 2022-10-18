import importlib
from typing import Optional, Tuple
from types import ModuleType
import sys
from multiprocessing import Value


def _get_module(
    module_name: str, python_path: Optional[str] = None
) -> Tuple[ModuleType, bool]:
    """Try and import the module name. Modify sys.path if required."""
    try:
        return importlib.import_module(module_name), False
    except ImportError as e:
        if python_path and python_path not in sys.path:
            sys.path.append(python_path)
            return importlib.import_module(module_name), True
        raise e


def _get_attr(
    module_name: str, attr_name: str, attr: Value, python_path: Optional[str] = None
):
    """
    Get the attribute from the module.
    """
    mod = _get_module(module_name, python_path)[0]
    attr_value = str(getattr(mod, attr_name)).encode() + b"\x00"
    attr[: len(attr_value)] = attr_value
