# Local additions to the hub configuration

Every `*.py` file here is loaded after the configuration of the template
(`hub/jupyterhub_config.py`, `load_subconfig`), in alphabetical order, with
the JupyterHub configuration object `c`. The files belong to the instance:
they are git-ignored and on the cruft skip list, so `cruft update` never
touches them. The directory is mounted read-only into the hub; restart the
hub after a change (`./adm_02_run.sh`).

Use them sparingly; whatever every instance needs belongs into the template.
