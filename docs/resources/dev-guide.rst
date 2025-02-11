Developer Guide
===============



.. highlight:: none

git Workflow
------------
You should use a `forking workflow <https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html>`_ to develop pfdf. In brief, you should make a fork of the official repository, and then create merge requests from the fork to the main branch of the official repository. These requests will then be reviewed before merging.


.. _dev-install:

Developer Installation
----------------------

.. admonition:: Prerequisites

    pfdf requires Python 3.11+, and these instructions assume you have also installed `git <https://git-scm.com/>`_.

We recommend using `poetry 2+ <https://python-poetry.org/>`_ to install pfdf. This will provide :ref:`various command line scripts <dev-scripts>` useful for developing the project.

You can install poetry using::

    pip install poetry

and see also the `poetry documentation <https://python-poetry.org/docs/#installation>`_ for additional installation instructions.

Next, clone your fork of the project and navigate to the cloned repository. Then, use::

    poetry install --with dev --extras tutorials

which will install pfdf, various development tools, and plotting libraries for the tutorials.


Gitlab Pipeline
---------------
The projected uses an automated Gitlab pipeline to ensure code quality, and to deploy various resources. The pipeline is defined in ``.gitlab-ci.yml`` and the stages are as follows:

**Build**

Builds and installs pfdf in the pipeline using ``poetry.lock``. Uses a parallel build matrix (defined in the ``.multiple-python-versions`` block) to install the project for each supported Python version.

**Test**

Checks code quality. Always runs the following tasks:

* ``safety``: Checks the dependencies for security vulnerabilities
* ``format``: Checks the code is formatted correctly
* ``test``: Runs the tests for each supported Python version. Requires 100% coverage.

This stage also includes the ``webtest`` job, which runs tests that depend on live, third-party APIs. This job only runs on merge requests and **should not** be run more frequently. 

**Tutorials**

Checks the tutorials are clean and working. Always checks the tutorials are clean (i.e. free of output, execution counts, and empty cells).

On merge requests, builds and runs the tutorials. This effectively checks the tutorials work with the current code, while minimizing computational expense. Running the tutorials can also be triggered manually.

**Deploy**

Tasks for deploying assets upon release. Whenever a new tag is created, the ``release`` task builds the Python distribution and uploads it to the Gitlab package registry. The optional ``pages`` job rebuilds and deploys the documentation. The ``pages`` job is manual to prevent documentation for in-progress code from overwriting the live docs.

Daily Build
+++++++++++
The ``daily-build`` branch should mirror the ``main`` branch and is used to implement a scheduled daily pipeline. The daily pipeline does not use ``poetry.lock`` to build the repository, and instead resolves dependencies from scratch. Effectively, the daily builds will use the most up-to-date versions of dependency libraries. This is intended to check if new releases of dependency libraries have broken compatibility with pfdf.

.. note::

    The daily build branch should remain distinct from the main branch to disambiguate MR pipeline badges from the daily build badges.



.. _dev-scripts:

Developer Scripts
-----------------
We use `poe <https://poethepoet.natn.io/>`_ to implement scripts for various developer tasks. These scripts are defined at the end of the ``pyproject.toml`` file. In general, you can run a poe script using::

    poe <script-name>

The following table summarizes the available scripts, and see the sections below for more details:

.. list-table::
    :header-rows: 1

    * - Command
      - Description
      - Used in Pipeline
    * - 
      -
      -
    * - **Dependencies**
      - 
      -
    * - safety
      - Checks that dependencies do not have security vulnerabilities
      - Yes
    * - update
      - Deletes ``poetry.lock`` and reinstalls the project
      - No
    * -
      -
      -
    * - **Formatting**
      -
      -
    * - format
      - Applies black and isort to the project
      - No
    * - lint
      - Raises an error if the project is not formatted correctly
      - Yes
    * -
      -
      -
    * - **Tests**
      - 
      -
    * - tests
      - Runs all non-web tests, and requires 100% coverage
      - Yes
    * - quicktest
      - Runs all tests that are neither slow, nor web.
      - No
    * - webtest
      - Runs only the web tests
      - Merge requests only
    * - coverage
      - Prints the testing coverage report
      - No
    * - htmlcov
      - Builds an HTML coverage report and opens in browser
      - No
    * -
      -
      -
    * - **Tutorials**
      -
      -
    * - tutorials
      - Opens the tutorials in Jupyter Lab
      - No
    * - clean-tutorials
      - Removes output, execution counts, and empty cells from the tutorial notebooks
      - No
    * - lint-tutorials
      - Raises an error if the tutorial notebooks are not clean
      - Yes
    * - setup-precommit
      - (Experimental) Sets up a pre-commit git hook that checks if the tutorials are clean
      - No
    * - 
      -
      -
    * - **Tutorial Builds**
      -
      -
    * - build-tutorials
      - Builds the tutorials
      - Implicitly via refresh-tutorials
    * - run-tutorials
      - Runs pre-built tutorials
      - Implicitly via refresh-tutorials
    * - refresh-tutorials
      - Rebuilds and runs the tutorials
      - Merge requests and building docs
    * - copy-tutorials
      - Copies built tutorials into the docs
      - When building docs
    * - 
      -
      -
    * - **Docs**
      -
      -
    * - docs
      - Rebuilds the documentation
      - No
    * - docs-all
      - Rebuilds the docs from scratch, rebuilding and running all tutorials
      - Manually triggered
    * - open-docs
      - Opens the docs in a web browser
      - No


.. _dev-deps:

Dependencies
------------
We use the ``pyproject.toml`` file to manage dependencies. This file is formatted for `poetry v2 <https://python-poetry.org/>`_. Developer dependencies are defined in the ``dev`` group, and the extra ``tutorials`` group includes non-essential dependencies used to run the tutorials. The ``safety`` script runs safety to check the dependencies for security dependencies, and will block the pipeline if the check fails. 

Separately, the ``update`` script will delete ``poetry.lock`` and reinstall the project from scratch (implicitly resolving all dependencies). This is intended to help ensure the lock file uses up-to-date dependencies.


.. _dev-format:

Formatting
----------
This project uses `isort <https://pycqa.github.io/isort/>`_ and `black <https://black.readthedocs.io/en/stable/>`_ to format the code. You can apply these formatters using the ``format`` script::

    poe format

Note that you can also run the ``lint`` script to check that the project meets these formatting requirements. This script is used by the Gitlab pipeline, and will block the pipeline if the check fails.

.. _dev-tests:

Testing
-------

This project uses the `pytest <https://docs.pytest.org/>`_ framework to implement tests. Before adding new code, the Gitlab pipeline requires:

1. All tests passing, and
2. 100% test coverage

So as a rule, all new code should include accompanying tests. The tests should follow a parallel structure to the pfdf package, and the tests for a given module should be named ``test_<module>.py``.

Within a test module, multiple tests for the same function should be grouped into a class. For large classes, the tests for each property or method should likewise be grouped into a class. For small classes, it may be appropriate to group all tests into a single class. Test class names should use capitalized camel-case. Underscores are discouraged, except when needed to distinguish between public and private routines with the same name. Individual tests should be named using standard Python snakecase (lowercase separated by underscores).

Note that you can check the status of the tests using::

    poe tests


Slow and Web Markers
++++++++++++++++++++
The project defines two custom `testing markers <https://docs.pytest.org/en/stable/example/markers.html>`_: ``slow`` and ``web``. All ``slow`` tests take a long time to run, and currently are exclusively applied to tests that require multiple CPUs. The ``web`` tests rely on external, third-party resources accessed over the internet.

All ``web`` tests are disabled in testing jobs by default, and are not included in test coverage. This ensures that the tests do not become reliant on third-party resources. That said, it is important to occasionally check that the web tests are passing (i.e. to ensure that third-party APIs have not changed). You can use the ``webtest`` script to run **only** these tests. The pipeline runs this script for merge requests only, minimizing reliance on third-party APIs while still ensuring they work.

Separately, you can use the ``quicktest`` script to run all tests *except* slow and web tests. This can be useful for checking that new updates run successfully while minimizing the time needed for tests to run.

.. _dev-tutorials:

Tutorials
---------
The tutorials are a set of `Jupyter notebooks <https://docs.jupyter.org/en/latest/>`_ designed to introduce new users to pfdf. Best practice is to only commit clean notebooks (i.e. notebooks without outputs, execution counts, or empty cells). The pipeline checks this is the case, but cannot prevent you from committing notebooks that fail these criteria.

Instead, you can use the ``setup-precommit`` script to establish a git pre-commit hook that will prevent commits that contain unclean tutorial notebooks. The script requires a unix-style path to a Python interpreter as input. Windows users should convert their path to a unix-style path before using this command. For example, if you are on Windows using conda, then this might resemble the following::

    /c/Users/MyUserName/.conda/envs/pfdf/python.exe

.. important::

    The pre-commit script is experimental. You **should** verify it works as expected before developing on the tutorials.

.. _dev-tutorial-builds:

The pipeline also builds and runs the tutorials, to ensure they work as expected. This copies the tutorials into a clean ``tutorial-builds`` folder, to ensure that the tutorials are run in a clean workspace. You can use the ``refresh-tutorials`` script to build and run the tutorials, or ``build-tutorials`` and ``run-tutorial`` to implement the individual tasks (often useful for troubleshooting tutorial builds).


.. _dev-docs:

Documentation
-------------

The documentation is built using `sphinx <https://www.sphinx-doc.org/en/master/index.html>`_ with the `furo <https://github.com/pradyunsg/furo>`_ theme. The content is written in `reStructuredText Markup (reST) <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_. You can find a nice `introduction to reST <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_ in the sphinx documentation, and the full documentation is here: `reST Specification <https://docutils.sourceforge.io/rst.html>`_.

The docs use the `sphinx_design <https://sphinx-design.readthedocs.io/en/rtd-theme/>`_ extension to enable dropdowns and tabbed panels within the content. The final website is deployed using `Gitlab Pages <https://docs.gitlab.com/ee/user/project/pages/>`_ via a manual job in the `Gitlab pipeline <https://docs.gitlab.com/ee/ci/pipelines/>`_. You must trigger this job manually to deploy new docs. The job will:

* Update the copyright to today's year
* Build and run the tutorials
* Copy the pre-run tutorials (with output) into the docs
* Run sphinx to generate the final HTML docs

You can run this process locally using the ``docs-all`` script. Alternatively, use the ``docs`` script to rebuild the docs without re-running the tutorials. This is useful when updating the documentation, as the tutorials take a while to run.

Finally, you can open the current HTML docs using the ``open-docs`` script.
