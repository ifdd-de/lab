
# --- IFDD lab (appended by images/default/Dockerfile) ---
# No requests outside the installation: no news feed, no update check
# (JupyterLab 4.6.6, LabApp.news_url and LabApp.check_for_updates_class).
c.LabApp.news_url = None  # noqa: F821
c.LabApp.check_for_updates_class = "jupyterlab.NeverCheckForUpdate"  # noqa: F821
