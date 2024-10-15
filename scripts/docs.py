"""
Scripts used to build the documentation
----------
Functions:
    locate_docs         - Returns the Path to the docs folder
    download_tutorials  - Downloads data for building the tutorials
    figures             - Builds the tutorial figures
"""

from pathlib import Path
import shutil
import subprocess
import os

import requests
import zipfile
import io


def locate_docs():
    return Path(__file__).parents[1] / "docs"


def download_tutorials():

    # Get URL and download path
    URL = "https://code.usgs.gov/ghsc/lhp/pfdf/-/raw/tutorial-data-2.0.0/tutorial-resources.zip?ref_type=heads&inline=false"
    docs = locate_docs()

    # Download and unzip
    web = requests.get(URL)
    zip = zipfile.ZipFile(io.BytesIO(web.content))
    zip.extractall(docs)


def figures():

    # Locate paths
    here = Path.cwd()
    docs = locate_docs()
    data = docs / "tutorial-resources" / "data"
    scripts = docs / "tutorial-resources" / "scripts"
    images = docs / "images"

    # Error if the data hasn't been downloaded
    if not data.exists():
        raise RuntimeError(
            'Cannot locate the tutorial data. Try running the "download_tutorials" '
            "command first."
        )

    # Move the tutorial scripts to the workspace
    if scripts.exists():
        shutil.rmtree(scripts)
    shutil.copytree(docs / "tutorials" / "scripts", scripts)

    # Move to the sandbox
    try:
        os.chdir(data)

        # Iterate through plotting tutorials. Delete existing figures
        tutorials = ["preprocess", "assessment"]
        for tutorial in tutorials:
            figures = images / tutorial
            if figures.exists():
                shutil.rmtree(figures)

            # Run the figure script
            script = scripts / f"{tutorial}_plots.py"
            subprocess.run(["python", str(script)], check=True)

            # Move the figures to the images folder
            os.mkdir(images / tutorial)
            files = os.listdir(data)
            for file in files:
                if file.endswith(".png"):
                    destination = images / tutorial / file
                    os.rename(file, destination)

    # Move back when finished
    finally:
        os.chdir(here)
