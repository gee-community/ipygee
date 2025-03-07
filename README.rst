
ipygee
======

.. |license| image:: https://img.shields.io/badge/License-MIT-yellow.svg?logo=opensourceinitiative&logoColor=white
    :target: LICENSE
    :alt: License: MIT

.. |commit| image:: https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg?logo=git&logoColor=white
   :target: https://conventionalcommits.org
   :alt: conventional commit

.. |ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :target: https://github.com/astral-sh/ruff
   :alt: ruff badge

.. |prettier| image:: https://img.shields.io/badge/code_style-prettier-ff69b4.svg?logo=prettier&logoColor=white
   :target: https://github.com/prettier/prettier
   :alt: prettier badge

.. |pre-commmit| image:: https://img.shields.io/badge/pre--commit-active-yellow?logo=pre-commit&logoColor=white
    :target: https://pre-commit.com/
    :alt: pre-commit

.. |pypi| image:: https://img.shields.io/pypi/v/ipygee?color=blue&logo=pypi&logoColor=white
    :target: https://pypi.org/project/ipygee/
    :alt: PyPI version

.. |build| image:: https://img.shields.io/github/actions/workflow/status/12rambau/ipygee/unit.yaml?logo=github&logoColor=white
    :target: https://github.com/12rambau/ipygee/actions/workflows/unit.yaml
    :alt: build

.. |coverage| image:: https://img.shields.io/codecov/c/github/12rambau/ipygee?logo=codecov&logoColor=white
    :target: https://codecov.io/gh/12rambau/ipygee
    :alt: Test Coverage

.. |docs| image:: https://img.shields.io/readthedocs/ipygee?logo=readthedocs&logoColor=white
    :target: https://ipygee.readthedocs.io/en/latest/
    :alt: Documentation Status

|license| |commit| |ruff| |prettier| |pre-commmit| |pypi| |build| |coverage| |docs|

Overview
--------

.. image:: https://raw.githubusercontent.com/gee-community/ipygee/main/docs/_static/logo.svg
    :width: 20%
    :align: right

This package provides interactive widgets object to interact with Google Earth engine from Python interactive environment.

TODO
----

This package is still a work in progress but beta testers are welcome. here are the different object that I would like to see implemented in this package:

- A very basic map with the most critical functions available (basically geemap core and that's all)
- A Task manager widget reproducing all the task manager features (and more?)
- A asset manager to manipulate GEE assets in an interactive window
- A bokhe interface (pure python) for all the geetools plotting capabilities
- A Map inspector (need the map first)
- A dataset Explorer (based on the geemap one but with an increased interactivity)
- All should be wired to JupyterLab sidecar for now, other IDE support will be welcome
- A complete and easy to use documentation
- If possible some CI tests (complicated for UI)

Credits
-------

This package was created with `Copier <https://copier.readthedocs.io/en/latest/>`__ and the `@12rambau/pypackage <https://github.com/12rambau/pypackage>`__ 0.1.16 project template.
