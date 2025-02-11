"""
Scripts used to build the documentation
----------
Functions:
    _docs           - Returns the Path to the docs
    add_copyright   - Updates the copyright with today's year
"""

import sys
from pathlib import Path
from datetime import date

def _docs():
    "Returns the path to the docs"

    return Path(__file__).parents[1] / "docs"

def add_copyright():
    "Updates the copyright with the current year"

    copyright = _docs() / "_static" / "copyright.css"
    content = (
        "/* Removes the copyright text enforced by the read-the-docs theme */\n"
        "div[class=copyright] {\n"
        "    visibility: hidden;\n"
        "    position: relative;\n"
        "}\n"
        "\n"
        "/* The desired attribution text */\n"
        "div[class=copyright]:after {\n"
        "    visibility: visible;\n"
        "    position: absolute;\n"
        "    top: 0;\n"
        "    left: 0;\n"
        f'    content: "USGS {date.today().year}, Public Domain";\n'
        "}\n"
    )
    copyright.write_text(content)




"Runs the indicated command from the CLI"
if __name__ == "__main__":
    here = sys.modules[__name__]
    command = getattr(here, sys.argv[1])
    command()

