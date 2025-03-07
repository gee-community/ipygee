"""The different types created for this specific package."""

import os
from pathlib import Path
from typing import Union

import ee
import geetools  # noqa: F401

pathlike = Union[os.PathLike, Path, ee.Asset]
