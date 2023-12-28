"""The asset manager widget code and functionalities."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import ee
import ipyvuetify as v
from google.cloud.resourcemanager import ProjectsClient


class AssetTreeView(v.Treeview):
    """A Google Earth Engine asset tree view widget."""

    def __init__(self, folders):
        """Initialize the asset tree view widget.

        Args:
            folders: the list of folders to display in the tree view as a list of dicts
                with the keys "id" and "name"
        """
        # restructure the folder list as a items list in a treeview object
        # each item is represented by a name, an id and a children list
        # that will be init to an empty list
        items = [{"name": f["name"], "id": f["id"], "children": []} for f in folders]

        # add icon management with a icon slots
        # see https://v2.vuetifyjs.com/en/components/treeview/#slots
        v_slots = [
            {
                "name": "prepend",
                "variable": "props",
                "children": [v.Icon(children=["mdi-folder"])],
            }
        ]

        super().__init__(items=items, v_slots=v_slots, dense=True, xs12=True)


class AssetManager(v.Flex):
    """The asset manager widget."""

    legacy_folders: List[Dict[str, str]]
    "The list of legacy folders as dicts with the keys 'id' and 'name'"

    gcloud_folders: List[Dict[str, str]]
    "The list of gcloud folders as dicts with the keys 'id' and 'name'"

    def __init__(self):
        """Initialize the asset manager widget."""
        # create a widget title
        w_title = v.Html(tag="h2", children=["Asset Manager"], xs12=True)

        # load all the folders and add them in alphabetic orders
        self.legacy_folders = self._get_legacy_folders()
        self.gcloud_folders = self._get_gcloud_folders()
        folders = sorted(
            self.legacy_folders + self.gcloud_folders, key=lambda f: f["name"]
        )
        w_tree_view = AssetTreeView(folders)

        super().__init__(children=[w_title, w_tree_view])

    @staticmethod
    def _get_legacy_folders() -> List[Dict[str, str]]:
        """Retrieve the list of folders in the legacy asset manager of GEE.

        Returns:
            the list of every legacy folder as dicts with the keys "id" and "name"
        """
        folders = [
            Path(f["id"]) for f in ee.data.getAssetRoots() if f["type"] == "Folder"
        ]
        return [{"id": f.as_posix(), "name": f.stem} for f in folders]

    @staticmethod
    def _get_gcloud_folders() -> List[Dict[str, str]]:
        folders = [
            p.project_id
            for p in ProjectsClient().search_projects()
            if "earth-engine" in p.labels
        ]
        return [{"id": f"project/{f}/assets", "name": f} for f in folders]
