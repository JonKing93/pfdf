Contributing
============

Contributions are welcome from the community. Questions can be asked on the
[issues page][1]. Before creating a new issue, please take a moment to search
and make sure a similar issue does not already exist. If one does exist, you
can comment (most simply even with just a `:+1:`) to show your support for that
issue.

If you have direct contributions you would like considered for incorporation
into the project you can [fork this repository][2] and
[submit a merge request][3] for review.

[1]: https://code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment/issues
[2]: https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html#creating-a-fork
[3]: https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html


## Formatting
This project uses `isort` and `black` to format the code. You can apply these formatters using:
```
poetry run format
```
This should format the code within the `pfdf` and `tests` directories. We also note that many IDEs include tools to automatically apply these formats. 

Note that you can also use:
```
poetry run check_format
```
to verify that all code is formatted correctly. The Gitlab pipeline requires that this check passes before code can be merged.


## Testing
This project uses the `pytest` framework to implement tests. You can test that the pure Python tests pass using:
```
poetry run tests
```
This will also report the test coverage and require a minimum coverage (defined in `dev_scripts.py`). The Gitlab pipeline requires that this script passes before code can be merged.

Note that the Gitlab pipeline does not check tests that rely on TauDEM commands. However, if TauDEM is installed, you can run all tests (pure Python and TauDEM reliant) using:
```
poetry run all_tests
```