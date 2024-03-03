"""The asset manager widget code and functionalities."""
from __future__ import annotations

from pathlib import Path
from typing import List

import ee
import geetools  # noqa
import ipyvuetify as v
import traitlets as t
from google.cloud.resourcemanager import ProjectsClient
from natsort import humansorted

from .decorator import switch
from .sidecar import HasSideCar

ICON_STYLE = {
    "PARENT": {"color": "black", "icon": "mdi-folder-open"},
    "PROJECT": {"color": "red", "icon": "mdi-google-cloud"},
    "FOLDER": {"color": "grey", "icon": "mdi-folder"},
    "IMAGE": {"color": "purple", "icon": "mdi-image-outline"},
    "IMAGE_COLLECTION": {"color": "purple", "icon": "mdi-image-multiple-outline"},
    "TABLE": {"color": "green", "icon": "mdi-table"},
    "FEATURE_COLLECTION": {"color": "green", "icon": "mdi-tabe"},
}
"The style to apply to each object"


class AssetManager(v.Flex, HasSideCar):
    """A asset manager widget."""

    # -- Variables -------------------------------------------------------------

    folder: t.Unicode = t.Unicode(".").tag(sync=True)
    "The current folder that the user see"

    selected_item: t.Unicode = t.Unicode("").tag(sync=True)
    "The selected item of the asset manager"

    sidecar_title = "Assets"
    "The title of the sidecar"

    # -- Widgets ---------------------------------------------------------------

    w_new: v.Btn
    "The new btn on the top of the asset manager"

    w_reload: v.Btn
    "The reload btn at the top of the asset manager"

    w_search: v.Btn
    "The search button to crowl into the existing items"

    w_selected: v.TextField
    "The field where the user can see the asset Id of the selected item"

    w_list: v.List
    "The list of items displayed in the asset manager"

    w_card: v.Card
    "The card hosting the list of items"

    def __init__(self):
        """Initialize the class."""
        # start by defining al the widgets
        # We deactivated the formatting to define each one of them on 1 single line
        # fmt: off

        # add a line of buttons to reload and add new projects
        self.w_new = v.Btn(color="error", children="NEW", elevation=2, class_="ma-1")
        self.w_reload = v.Btn(children=[v.Icon(color="primary", children="mdi-reload")], elevation=2, class_="ma-1")
        self.w_search = v.Btn(children=[v.Icon(color="primary", children="mdi-magnify")], elevation=2, class_="ma-1")
        w_main_line = v.Flex(children=[self.w_new, self.w_reload, self.w_search])

        # generate the asset selector and the CRUD buttons
        self.w_selected = v.TextField(readonly=True, placeholder="Selected item", v_model="", clearable=True, outlined=True, class_="ma-1")
        self.w_view = v.Btn(children=[v.Icon(color="primary", children="mdi-eye")])
        self.w_copy = v.Btn(children=[v.Icon(color="primary", children="mdi-content-copy")])
        self.w_move = v.Btn(children=[v.Icon(color="primary", children="mdi-file-move")])
        self.w_delete = v.Btn(children=[v.Icon(color="primary", children="mdi-trash-can")])
        w_btn_list = v.ItemGroup(class_="ma-1 v-btn-toggle",children=[self.w_view, self.w_copy, self.w_move, self.w_delete])
        w_selected_line = v.Layout(row=True, children=[w_btn_list, self.w_selected], class_="ma-1")

        # generate the initial list
        w_group = v.ListItemGroup(children=self.get_items(), v_model="")
        self.w_list = v.List(dense=True, v_model=True, children=[w_group], outlined=True)
        self.w_card = v.Card(children=[self.w_list], outlined=True, class_="ma-1")

        super().__init__(children=[w_main_line, w_selected_line, self.w_card], v_model="", class_="ma-1")
        # fmt: on

        # update the template of the DOM object to add a js method to copy to clipboard
        # template with js behaviour
        js_dir = Path(__file__).parent / "js"
        clip = (js_dir / "jupyter_clip.js").read_text()
        self.template = "<mytf/>" "<script>{methods: {jupyter_clip(_txt) {%s}}}</script>" % clip

        # add JS behaviour
        t.link((self, "selected_item"), (self, "v_model"))
        self.w_list.children[0].observe(self.on_item_select, "v_model")
        self.w_reload.on_event("click", self.on_reload)
        self.w_copy.on_event("click", self.on_copy)

    def get_items(self) -> List[v.ListItem]:
        """Create the list of items inside a folder."""
        # special case when we are at the root of everything
        # because of the specific display of cloud projects we will store both the name and the id of everything as a dict
        # for all other item types it will simply be the Name
        if self.folder == ".":
            list_items = [p.project_id for p in ProjectsClient().search_projects() if "earth-engine" in p.labels]  # fmt: skip
            list_items = [{"id": f"projects/{i}/assets", "name": i} for i in list_items]
        else:
            list_items = [{"id": str(i), "name": i.name} for i in ee.Asset(self.folder).iterdir()]

        # split the folders and the files to display the folders first
        # cloud bucket will be considered as folders
        folder_list, file_list = [], []  # type: ignore[var-annotated]

        # walk the list of items and generate a list of ListItem using all the appropriate features
        # first we extract the type to deduce the icon and color, then we build the Items with the
        # ID and the display name and finally we split them in 2 groups the folders and the files
        for i in list_items:
            asset = ee.Asset(i["id"])
            type = "PROJECT" if asset.is_project() else asset.type
            icon = ICON_STYLE[type]["icon"]
            color = ICON_STYLE[type]["color"]

            action = v.ListItemAction(children=[v.Icon(color=color, children=[icon])], class_="mr-1")
            content = v.ListItemContent(children=[v.ListItemTitle(children=[i["name"]])])
            dst_list = folder_list if type in ["FOLDER", "PROJECT"] else file_list
            dst_list.append(v.ListItem(value=i["id"], children=[action, content]))

        # humanly sort the 2 lists so that number are treated nicely
        folder_list = humansorted(folder_list, key=lambda x: x.value)
        file_list = humansorted(file_list, key=lambda x: x.value)

        # add a parent items if necessary. We follow the same mechanism with specific verifications
        # if the parent is a project folder or the root
        if self.folder != ".":
            icon = ICON_STYLE["PARENT"]["icon"]
            color = ICON_STYLE["PARENT"]["color"]

            asset = ee.Asset(self.folder)
            parent = ee.Asset("") if asset.is_project() else asset.parent
            name = parent.parts[1] if parent.is_project() else parent.name
            name = name or "."  # special case for the root

            action = v.ListItemAction(children=[v.Icon(color=color, children=[icon])], class_="mr-1")
            content = v.ListItemContent(children=[v.ListItemTitle(children=[name])])
            item = v.ListItem(value=str(parent), children=[action, content])

            folder_list.insert(0, item)

        # return the concatenation of the 2 lists
        return folder_list + file_list

    @switch("loading", "disabled", member="w_card")
    def on_item_select(self, change: dict):
        """Act when an item is clicked by the user."""
        # reset the copy button status
        self.w_copy.children[0].children = ["mdi-content-copy"]

        # exit if nothing is changed to avoid infinite loop upon loading
        selected = change["new"]
        if not selected:
            return

        # select the item in the item TextField so user can interact with it
        self.w_selected.v_model = change["new"]

        # reset files. This is resetting the scroll to top without using js scripts
        # set the new content files and folders
        ee.Asset(change["new"])
        if selected == "." or ee.Asset(selected).is_project() or ee.Asset(selected).is_folder():
            self.folder = selected
            items = self.get_items()
            self.w_list.children[0].children = []  # trick to scroll up
            self.w_list.children[0].children = items

    def on_reload(self, *args):
        """Reload the current folder."""
        self.on_item_select(change={"new": self.folder})

    def on_copy(self, *args):
        """Copy the selected item to clipboard."""
        self.send({"method": "clip", "args": [self.w_selected.v_model]})
        self.w_copy.children[0].children = ["mdi-check"]
