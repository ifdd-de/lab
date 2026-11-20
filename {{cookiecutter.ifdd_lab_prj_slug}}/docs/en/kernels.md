(ifdd-lab-kernels)=
# Images of the user servers
{%- set internet = cookiecutter.ifdd_lab_internet == "y" %}

## What every image contains

Every image under `images/<name>/` is based on
`{{ cookiecutter.ifdd_lab_kernel_base_image }}` (Jupyter Docker Stacks) and
adds:

- the CA certificates of `certs/`, used by Python's `ssl`, `requests` and
  `pip`;
- the packages of `requirements.txt` (those of the papermill runner of
  `ifdd-de/wf`, so a notebook sees the same libraries in both places);
{%- if internet %}
- the Git panel of JupyterLab (`requirements-git.txt`);
{%- endif %}
- the helper `ifdd_lab`;
- JupyterLab without news feed and update check.

The base brings `git`, `pandoc` and XeLaTeX: File, Save and Export Notebook
As, PDF produces a PDF through LaTeX. The same works on the command line:

```bash
jupyter nbconvert --to pdf notebook.ipynb
```

## Calling IFDD services

```python
import ifdd_lab

be = ifdd_lab.session()                     # ifdd-be at IFDD_BE_URL
print(be.get("/whoami").json())             # roles and context patterns of your token
r = be.get("/nodes/", params={"start": 0, "end": 10})
```

`ifdd_lab.session(base_url)` works for any service that accepts the token;
`ifdd_lab.access_token()` returns the token itself. Both raise
`ifdd_lab.LoginRequired` when the hub has no valid tokens for the user any
more. `examples/notebooks/backend_with_your_rights.ipynb` shows the calls;
upload it in JupyterLab.

## Another image

1. Copy `images/default/` to `images/<name>/` and change it (packages in
   `requirements.txt`, system packages in the `Dockerfile`).
2. Add the name to the variable `ifdd_lab_images` and apply it with
   `cruft update` (or `ifdd-meta update`): the compose file then builds it
   and the hub offers it.
3. `./adm_01_build.sh`, then `./adm_02_run.sh`.

With more than one image the hub asks for the image when a server starts.
