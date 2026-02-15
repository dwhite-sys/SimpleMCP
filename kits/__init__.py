# Kits package: auto-discover and import every kit module so their
# @tool decorators fire at import time and register tools.

import importlib
import pkgutil
import pathlib


def _auto_import_kits():
    """
    Dynamically import every .py module inside the kits/ package.
    Each module that uses the @tool decorator will have its tools
    registered in the global TOOLS registry automatically on import.
    """
    package_dir = pathlib.Path(__file__).resolve().parent

    for finder, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        # Skip __init__ itself
        if module_name.startswith("_"):
            continue
        importlib.import_module(f".{module_name}", package=__name__)


# Run auto-discovery on package import
_auto_import_kits()

# --- Manual kit imports (no longer needed) ---
# from . import sqlite_kit
# from . import web_kit