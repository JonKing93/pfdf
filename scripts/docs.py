from pathlib import Path
import shutil
import subprocess
import sys
import webbrowser
import os
import tomllib

from . import run


def locate_docs():
    return Path(__file__).parents[1] / "docs"


def locate_build():
    root = locate_docs()
    return root.parent / "public"


def build():
    "Deletes old docs, then builds new docs. Returns path to new build"

    # Locate the build folder and delete any contents
    build = locate_build()
    if build.exists():
        shutil.rmtree(build)

    # Use sphinx to rebuild the docs
    root = locate_docs()
    subprocess.run(["sphinx-build", "-qa", str(root), str(build)])


def open_docs():
    "Opens indicated page of docs"

    build = locate_build()
    args = sys.argv
    if len(args) == 1:
        page = "index"
    else:
        page = args[1]
    webbrowser.open(build / f"{page}.html")


def rebuild():
    "Builds docs, then opens to index or page"
    build()
    open_docs()


def figures():

    # Locate paths
    here = Path.cwd()
    docs = locate_docs()
    data = docs / "tutorials" / "download" / "data"
    images = docs / "images"

    # Move to the sandbox
    try:
        os.chdir(data)

        # Iterate through plotting tutorials. Delete existing figures
        tutorials = ["assessment", "preprocess"]
        for tutorial in tutorials:
            figures = images / tutorial
            if figures.exists():
                shutil.rmtree(figures)

            # Run the figure script
            script = data.parent / "code" / f"{tutorial}_plots.py"
            run(["python", str(script)])

            # Move the figures to the images folder
            os.mkdir(images/tutorial)
            files = os.listdir(data)
            for file in files:
                if file.endswith('.png'):
                    destination = images / tutorial / file
                    os.rename(file, destination)

    # Move back when finished
    finally:
        os.chdir(here)


def check_version():
    "Checks that the release in conf.py matches the version in pyproject.toml"

    # Get the version string from pyproject.toml
    docs = locate_docs()
    pyproject = docs.parent / "pyproject.toml"
    with open(pyproject, 'rb') as file:
        pyproject = tomllib.load(file)
    version = pyproject['tool']['poetry']['version']

    # Get the release string from conf.py
    conf = docs / "conf.py"
    with open(conf) as file:
        conf = file.read()
    release = '\nrelease = "'
    start = conf.find(release) + len(release)
    conf = conf[start:]
    stop = conf.find('"')
    release = conf[:stop]

    # Require them to be the same
    if version != release:
        raise Exception(
            f"The version string in pyproject.toml ({version}) does not match the "
            f"release string in conf.py ({release})"
        )
    