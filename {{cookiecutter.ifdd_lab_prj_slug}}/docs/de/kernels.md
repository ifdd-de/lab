(ifdd-lab-kernels)=
# Images der Benutzer-Server
{%- set internet = cookiecutter.ifdd_lab_internet == "y" %}

## Was jedes Image enthält

Jedes Image unter `images/<name>/` baut auf
`{{ cookiecutter.ifdd_lab_kernel_base_image }}` (Jupyter Docker Stacks) auf
und ergänzt:

- die CA-Zertifikate aus `certs/`, genutzt von Pythons `ssl`, `requests` und
  `pip`;
- die Pakete aus `requirements.txt` (die des papermill-Runners von
  `ifdd-de/wf`, damit ein Notebook an beiden Orten dieselben Bibliotheken
  sieht);
{%- if internet %}
- das Git-Panel von JupyterLab (`requirements-git.txt`);
{%- endif %}
- den Helfer `ifdd_lab`;
- JupyterLab ohne Neuigkeiten-Feed und Update-Prüfung.

Die Basis bringt `git`, `pandoc` und XeLaTeX mit: File, Save and Export
Notebook As, PDF erzeugt ein PDF über LaTeX. Auf der Kommandozeile geht das
ebenso:

```bash
jupyter nbconvert --to pdf notebook.ipynb
```

## IFDD-Dienste aufrufen

```python
import ifdd_lab

be = ifdd_lab.session()                     # ifdd-be unter IFDD_BE_URL
print(be.get("/whoami").json())             # Rollen und Kontextmuster des eigenen Tokens
r = be.get("/nodes/", params={"start": 0, "end": 10})
```

`ifdd_lab.session(base_url)` funktioniert für jeden Dienst, der das Token
annimmt; `ifdd_lab.access_token()` liefert das Token selbst. Beide melden
`ifdd_lab.LoginRequired`, wenn der Hub keine gültigen Tokens für den
Benutzer mehr hat. `examples/notebooks/backend_with_your_rights.ipynb` zeigt
die Aufrufe; in JupyterLab hochladen.

## Ein weiteres Image

1. `images/default/` nach `images/<name>/` kopieren und anpassen (Pakete in
   `requirements.txt`, Systempakete im `Dockerfile`).
2. Den Namen in die Variable `ifdd_lab_images` aufnehmen und mit
   `cruft update` (oder `ifdd-meta update`) anwenden: Dann baut die
   Compose-Datei das Image, und der Hub bietet es an.
3. `./adm_01_build.sh`, dann `./adm_02_run.sh`.

Gibt es mehr als ein Image, fragt der Hub beim Start eines Servers danach.
