"""A meta class to define DOM element that can be send to the sidecar."""
from __future__ import annotations

from IPython.display import display
from sidecar import Sidecar


class HasSideCar:
    """MetClass to define the to_sidecar method."""

    sidecar_title = "Sidecar"
    "The title of the sidecar"

    def to_sidecar(self):
        """Send the widget to a sidecar."""
        with Sidecar(title=self.sidecar_title):
            display(self)
