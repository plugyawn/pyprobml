import pytest
import os
import re
import subprocess
import warnings
from time import time
import shutil
from testbook import testbook

# Global variables
TIMEOUT = 600  # seconds
TEST_DIR = "test_results"
os.environ["FIG_DIR"] = "figures"
os.environ["LATEXIFY"] = ""  # To enable latexify code
os.environ["DUAL_SAVE"] = ""  # To save both .pdf and .png

# Load notebooks
cmd = "git ls-files 'notebooks/book**.ipynb' -z | xargs -0 -n1 -I{} -- git log -1 --format='%at {}' {}"
notebooks_raw = subprocess.run(cmd, check=True, shell=True, capture_output=True, text=True)
if notebooks_raw.stderr:
    warnings.warn(notebooks_raw.stderr)
timestamped_notebooks = []
for entry in notebooks_raw.stdout.split("\n"):
    if entry:
        timestamped_notebooks.append(entry.split(" "))
timestamped_notebooks.sort(reverse=True)  # execute newer notebooks first
notebooks = [
    notebook
    for i, (_, notebook) in enumerate(timestamped_notebooks)
    if i % 20 == int(os.environ["PYPROBML_GA_RUNNER_ID"])
]

# To make subprocess stdout human readable
# https://stackoverflow.com/a/38662876
def escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


# To update workflow status for a figure
def save_status(full_path, icon):
    full_path = os.path.join(TEST_DIR, full_path)
    if not os.path.exists(os.path.dirname(full_path)):
        os.makedirs(os.path.dirname(full_path))
    save_name = full_path.replace(".ipynb", ".png")
    shutil.copy("tests/icons/{}.png".format(icon), save_name)


# Parameterize notebooks
@pytest.mark.parametrize("notebook", notebooks)
def test_run_notebooks(notebook):
    """
    Test notebooks
    """
    init = time()
    try:

        @testbook(notebook, execute=True, timeout=TIMEOUT)
        def check(tb):
            pass

        check()
        save_status(notebook, "right")
        print("passed in {:.2f} seconds: {} ".format(time() - init, notebook))
    except Exception as e:
        save_status(notebook, "wrong")
        print("failed after {:.2f} seconds: {} ".format(time() - init, notebook))
        with open(f"{TEST_DIR}/{notebook.replace('.ipynb', '.log')}", "w") as f:
            f.write(escape_ansi(str((e))))
        raise e
