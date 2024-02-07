Developer Guide
===============

.. highlight:: none

git Workflow
------------
You should use a `forking workflow <https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html>`_ to develop pfdf. In brief, you should make a fork of the official repository, and then create merge requests from the fork to the main branch of the official repository. These requests will then be reviewed before merging.


.. _dev-install:

Installation
------------

.. admonition:: Prerequisites

    pfdf requires Python 3.11+, and these instructions assume you have also installed `git <https://git-scm.com/>`_.

We recommend using `poetry <https://python-poetry.org/>`_ to install pfdf. This will provide :ref:`various command line scripts <dev-scripts>` useful for developing the project.

You can install poetry using::

    pip install poetry

and see also the `poetry documentation <https://python-poetry.org/docs/#installation>`_ for additional installation instructions.

Next, clone your fork of the project and navigate to the cloned repository. Then, use::

    poetry install --with dev --extras tutorials

which will install pfdf, various development tools, and plotting libraries for the tutorials.



Formatting
----------
This project uses `isort <https://pycqa.github.io/isort/>`_ and `black <https://black.readthedocs.io/en/stable/>`_ to format the code. You can apply these formatters using::

    poetry run format

This should format the code within the ``pfdf`` and ``tests`` directories. We also note that many IDEs include tools to automatically apply these formats. 

Note that you can also use::

    poetry run lint

to verify that all code is formatted correctly. The Gitlab pipeline requires that this check passes before code can be merged.


Testing
-------

This project uses the `pytest <https://docs.pytest.org/>`_ framework to implement tests. Before adding new code, the Gitlab pipeline requires:

1. All tests passing, and
2. 100% test coverage

So as a rule, all new code should include accompanying tests. The tests should follow a parallel structure to the pfdf package, and the tests for a given module should be named ``test_<module>.py``.

Within a test module, multiple tests for the same function should be grouped into a class. For large classes, the tests for each property or method should likewise be grouped into a class. For small classes, it may be appropriate to group all tests into a single class. Test class names should use capitalized camel-case. Underscores are discouraged, except when needed to distinguish between public and private routines with the same name. Individual tests should be named using standard Python snakecase (lowercase separated by underscores).

Note that you can check the status of the tests using::

    poetry run tests


Documentation
-------------

The documentation is built using `sphinx <https://www.sphinx-doc.org/en/master/index.html>`_ with the `read-the-docs theme <https://sphinx-rtd-theme.readthedocs.io/en/stable/>`_. The content is written in `reStructuredText Markup (reST) <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_. You can find a nice `introduction to reST <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_ in the sphinx documentation, and the full documentation is here: `reST Specification <https://docutils.sourceforge.io/rst.html>`_.

The docs use the `sphinx_design <https://sphinx-design.readthedocs.io/en/rtd-theme/>`_ extension to enable dropdowns and tabbed panels within the content. The final website is deployed using `Gitlab Pages <https://docs.gitlab.com/ee/user/project/pages/>`_ via a manual job in the `Gitlab pipeline <https://docs.gitlab.com/ee/ci/pipelines/>`_. You must trigger this job manually to deploy new docs. The job will:

* Check that the docs release matches the release in ``pyproject.toml``
* Generate figures for the tutorials, and then
* Run sphinx to generate the final HTML docs

You can run the individual tasks using::

    poetry run version
    poetry run figures
    poetry run docs

The ``rebuild`` script is also useful when editing the docs. This will re-run sphinx and open the indicated page in a web browser. For example::

    poetry run rebuild

will open to the root of the docs, and::

    poetry run rebuild tutorials/assessment

will open to the page for the hazard assessment tutorial.


Pipeline Scripts
----------------

You can run the safety check, linting, and testing jobs using::

    poetry run pipeline

Alternatively, use::

    poetry run docs_pipeline

to also check the documentation version string, generate figures, and rebuild the docs.



.. _dev-scripts:

Scripts
-------
The following is a complete list of available developer scripts:

**Code Tasks**

.. list-table::

    * - **Command**
      - **Description**
      - **Used in pipeline**
    * -
      -
      -
    * - **Code quality**
      -
      -
    * - safety
      - Checks for security vulnerabilities
      - Yes
    * - lint
      - Checks the formatting of pfdf and tests
      - Yes
    * - format
      - Applies formatters to pfdf and tests
      - No
    * - tests
      - Runs tests and requires 100% coverage
      - Yes
    * -
      -
      -
    * - **Documentation**
      -
      -
    * - docs
      - Builds the docs, deleting current docs if they exist
      - Docs job (Manually triggered)
    * - open
      - Opens the docs to the indicated page in a browser
      - No
    * - rebuild
      - Rebuilds the docs, then opens to the indicated page
      - No
    * - figures
      - Runs the tutorial scripts and generates figures
      - Docs job (Manually triggered)
    * - version
      - Checks that the release string in the docs matches the project
      - Docs job (Manually triggered)
    * -
      -
      -
    * - **Pipelines**
      - Mimic Gitlab pipelines
      -
    * - pipeline
      - Runs ``safety``, ``lint``, and ``tests``
      - Merge requests
    * - docs_pipeline
      - Also runs ``version``, ``figures``, and ``docs``
      - Manually triggered

    

