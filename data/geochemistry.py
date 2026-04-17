# -*- coding: utf-8 -*-
"""Compatibility shim for legacy imports of data.geochemistry.

The geochemistry implementation now lives in the data/geochemistry/ package.
This file exists for tooling that still imports by file path.
"""
import importlib.util as _importlib_util
import sys as _sys
from pathlib import Path as _Path

_pkg_dir = _Path(__file__).with_name("geochemistry")
_pkg_init = _pkg_dir / "__init__.py"
if not _pkg_init.exists():
    raise ImportError("Failed to locate geochemistry package implementation.")

_sys.modules.pop(__name__, None)
_spec = _importlib_util.spec_from_file_location(
    __name__,
    _pkg_init,
    submodule_search_locations=[str(_pkg_dir)],
)
if _spec is None or _spec.loader is None:
    raise ImportError("Failed to load geochemistry package implementation.")

_module = _importlib_util.module_from_spec(_spec)
_sys.modules[__name__] = _module
_spec.loader.exec_module(_module)

globals().update(_module.__dict__)

del _importlib_util, _sys, _Path, _pkg_dir, _pkg_init, _spec, _module
