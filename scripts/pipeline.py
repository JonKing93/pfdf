
from .dev import safety, lint, tests
from .docs import check_version, build, figures


def pipeline():
    "Runs the steps of the Gitlab pipeline"
    safety()
    lint()
    tests()

def docs_pipeline():
    "Also attempts to build the docs"
    pipeline()
    check_version()
    figures()
    build()
