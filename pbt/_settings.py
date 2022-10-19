import json
from typing import Optional


def load_settings(json_paths, settings: Optional[dict] = None):
    """
    Return settings from the given JSON files as a dictionary.
    This does not expand placeholders.
    Call expand_all_placeholders on the data after merging.
    This allows variables such as the version to be modified in code.
    """
    if settings is not None:
        settings = dict(settings)
    for json_path in json_paths:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        settings = data if settings is None else _merge(settings, data)
    return settings


def expand_all_placeholders(settings):
    """
    This function expands placeholders: That is, if a settings file contains

        {
            "app_name": "MyApp",
            "freeze_dir": "target/${app_name}"
        }

    then "freeze_dir" in the result of this function is "target/MyApp".

    It also merges lists. Say base.json contains

        { "hidden_imports": ["a"] }

    and mac.json contains

        { "hidden_imports": ["b"] }

    then you obtain

        { "hidden_imports": ["a", "b'] }.
    """
    while True:
        for key, value in settings.items():
            new_value = expand_placeholders(value, settings)
            if new_value != value:
                settings[key] = new_value
                break
        else:
            break
    return settings


def expand_placeholders(obj, settings, template="${%s}"):
    if isinstance(obj, str):
        for key, value in settings.items():
            obj = obj.replace(template % key, str(value))
    elif isinstance(obj, list):
        return [expand_placeholders(o, settings) for o in obj]
    elif isinstance(obj, dict):
        return {k: expand_placeholders(v, settings) for k, v in obj.items()}
    return obj


def _merge(a, b):
    if type(a) != type(b):
        raise ValueError("Cannot merge %r and %r" % (a, b))
    if isinstance(a, list):
        return a + b
    if isinstance(a, dict):
        result = dict(a)
        for k, v in b.items():
            result[k] = _merge(a[k], v) if k in a else v
        return result
    return b
