from __future__ import annotations

import ctypes
import importlib.util
import os


def _preload() -> None:
    spec = importlib.util.find_spec("IfxPy")
    if not (spec and spec.origin):
        return
    site_packages = os.path.dirname(os.path.dirname(spec.origin))
    driver_lib = os.path.join(site_packages, "onedb-odbc-driver", "lib")
    load_order = [
        os.path.join(driver_lib, "esql", "libifgls.so"),
        os.path.join(driver_lib, "esql", "libifos.so"),
        os.path.join(driver_lib, "esql", "libifgen.so"),
        os.path.join(driver_lib, "cli", "libifcli.so"),
        os.path.join(driver_lib, "cli", "libthcli.so"),
    ]
    for so in load_order:
        if os.path.isfile(so):
            ctypes.CDLL(so, mode=ctypes.RTLD_GLOBAL)


_preload()

# Made with Bob
