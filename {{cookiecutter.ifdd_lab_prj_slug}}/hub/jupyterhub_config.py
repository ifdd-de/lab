# JupyterHub configuration of this instance. The settings live in
# ifdd_lab_hub.py (from the template, the same in every instance); local
# additions go into hub/config.d/*.py, which cruft update never touches.
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ifdd_lab_hub  # noqa: E402

c = get_config()  # noqa: F821 - provided by JupyterHub
ifdd_lab_hub.configure(c)

for extra in sorted((HERE / "config.d").glob("*.py")):
    load_subconfig(str(extra))  # noqa: F821 - provided by JupyterHub
