"""The init file of the package."""

__version__ = "0.0.0"
__author__ = "Pierrick Rambaud"
__email__ = "pierrick.rambaud49@gmail.com"

# import in the main class the extensions built for the different GEE native classes
from .ee_feature_collection import FeatureCollectionAccessor
from .ee_image import ImageAccessor
from .ee_image_collection import ImageCollectionAccessor
