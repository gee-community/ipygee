"""The asset manager widget code and functionalities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import ee
import geetools  # noqa
import ipyvuetify as v
import requests
import traitlets as t
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

    w_delete_dialog: v.Dialog
    "The dialog to confirm the deletion of an asset"

    w_move_dialog: v.Dialog
    "The dialog to confirm the move of an asset"

    w_asset_dialog: v.Dialog
    "The dialog to view an asset"

    w_create_dialog: v.Dialog
    "The dialog to create a new folder"

    def __init__(self):
        """Initialize the class."""
        # start by defining al the widgets
        # We deactivated the formatting to define each one of them on 1 single line
        # fmt: off

        # add a line of buttons to reload and add new projects
        self.w_new = v.Btn(color="error", children="NEW", elevation=2, class_="ml-1", disabled=True, small=True)
        self.w_reload = v.Btn(children=[v.Icon(color="primary", children="mdi-reload", small=True)], elevation=2, class_="ma-1", small=True)
        self.w_search = v.Btn(children=[v.Icon(color="primary", children="mdi-magnify", small=True)], elevation=2, class_="mr-1", disabled=True, small=True)
        w_main_line = v.Flex(children=[self.w_new, self.w_reload, self.w_search])

        # generate the asset selector and the CRUD buttons
        self.w_selected = v.TextField(readonly=True, label="Selected item", v_model="", clearable=True, outlined=True, class_="mt-1")
        self.w_view = v.Btn(children=[v.Icon(color="primary", children="mdi-eye", small=True)], disabled=True, small=True)
        self.w_copy = v.Btn(children=[v.Icon(color="primary", children="mdi-content-copy", small=True)], disabled=True, small=True)
        self.w_move = v.Btn(children=[v.Icon(color="primary", children="mdi-file-move", small=True)], disabled=True, small=True)
        self.w_delete = v.Btn(children=[v.Icon(color="primary", children="mdi-trash-can", small=True)], disabled=True, small=True)
        w_btn_list = v.ItemGroup(class_="ma-1 v-btn-toggle",children=[self.w_view, self.w_copy, self.w_move, self.w_delete])

        # generate the initial list
        w_group = v.ListItemGroup(children=self.get_items(), v_model="")
        self.w_list = v.List(dense=True, v_model=True, children=[w_group], outlined=True)
        self.w_card = v.Card(children=[self.w_list], outlined=True, class_="ma-1")

        # create the hidden dialogs
        self.w_delete_dialog = DeleteAssetDialog()
        self.w_move_dialog = MoveAssetDialog()
        self.w_asset_dialog = AssetDialog()
        self.w_create_dialog = CreateFolderDialog()

        super().__init__(children=[
            self.w_delete_dialog, self.w_move_dialog, self.w_asset_dialog, self.w_create_dialog,
            w_main_line, w_btn_list, self.w_selected, self.w_card
        ], v_model="", class_="ma-1")
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
        self.w_delete_dialog.observe(self.on_reload, "value")
        self.w_copy.on_event("click", self.on_copy)
        self.w_delete.on_event("click", self.on_delete)
        self.w_selected.observe(self.activate_buttons, "v_model")
        self.w_move.on_event("click", self.on_move)
        self.w_view.on_event("click", self.on_view)
        self.w_new.on_event("click", self.on_new)

    def get_projects(self) -> List:
        """Get the list of project accessible from the authenticated user."""
        # recover the saved credentials of the user from the file system
        credential_path = Path.home() / ".config" / "earthengine" / "credentials"
        creds = json.loads(credential_path.read_text())

        # get an authentication token for this very account and make requests to the Google
        # REST API
        url = "https://cloudresourcemanager.googleapis.com/v1/projects"
        token_url = "https://oauth2.googleapis.com/token"
        creds["grant_type"] = "refresh_token"
        response = requests.post(token_url, data=creds)

        if response.status_code == 200:
            access_token = response.json().get("access_token")
        else:
            raise ValueError(f"Failed to retrieve access token: {response.text}")

        # Define the API endpoint and headers and list all the projects available
        cloud_resource_manager_url = "https://cloudresourcemanager.googleapis.com/v1/projects"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(cloud_resource_manager_url, headers=headers)

        # Handle the response
        if response.status_code == 200:
            projects = [p["projectId"] for p in response.json()["projects"]]
        else:
            raise ValueError(f"API request failed: {response.text}")

        # filter out the projects that are not compatible with GEE
        url = "https://serviceusage.googleapis.com/v1/projects/{}/services/earthengine.googleapis.com"
        gee_projects = []
        for p in projects:
            response = requests.get(url.format(p), headers=headers)
            if response.status_code == 200:
                gee_projects.append(p)

        return gee_projects

    def get_items(self) -> List[v.ListItem]:
        """Create the list of items inside a folder."""
        # special case when we are at the root of everything
        # because of the specific display of cloud projects we will store both the name and the id of everything as a dict
        # for all other item types it will simply be the Name
        if self.folder == ".":
            list_items = [{"id": f"projects/{i}/assets", "name": i} for i in self.get_projects()]
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

            action = v.ListItemAction(children=[v.Icon(color=color, small=True, children=[icon])], class_="mr-1")
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

            action = v.ListItemAction(children=[v.Icon(color=color, small=True, children=[icon])], class_="mr-1")
            content = v.ListItemContent(children=[v.ListItemTitle(children=[name])])
            item = v.ListItem(value=str(parent), children=[action, content])

            folder_list.insert(0, item)

        # return the concatenation of the 2 lists
        return folder_list + file_list

    @switch("loading", "disabled", member="w_card")
    def on_item_select(self, change: dict):
        """Act when an item is clicked by the user."""
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
        try:
            self.on_item_select(change={"new": self.folder})
        except ValueError: 
            self.on_item_select(change={"new": ee.Asset(self.folder).parent.as_posix()})
        
    def on_copy(self, *args):
        """Copy the selected item to clipboard."""
        self.send({"method": "clip", "args": [self.w_selected.v_model]})
        self.w_copy.children[0].children = ["mdi-check"]

    @switch("loading", "disabled", member="w_card")
    def on_delete(self, *args):
        """Delete the selected item.

        Ask for confirmation before deleting via a dialog window.
        """
        # make sure the current item is deletable. We can only delete assets i.e.
        # files and folders. Projects and buckets are not deletable.
        selected = self.w_selected.v_model
        if selected in [".", ""] or ee.Asset(selected).is_project():
            return

        # open the delete dialog with the current file
        self.w_delete_dialog.reload(ee.Asset(selected))
        self.w_delete_dialog.value = True

    @switch("loading", "disabled", member="w_card")
    def on_move(self, *args):
        """Copy the selected item.

        Ask for confirmation before moving via a dialog window.
        """
        # make sure the current item is moveable. We can only move assets i.e.
        # files and folders. Projects and buckets are not deletable.
        selected = self.w_selected.v_model
        if selected in [".", ""] or ee.Asset(selected).is_project():
            return

        # open the delete dialog with the current file
        self.w_move_dialog.reload(ee.Asset(selected))
        self.w_move_dialog.value = True

    @switch("loading", "disabled", member="w_card")
    def on_view(self, *args):
        """Open the view dialog."""
        # make sure the current item is moveable. We can only move assets i.e.
        # files and folders. Projects and buckets are not deletable.
        selected = ee.Asset(self.w_selected.v_model)
        if self.w_selected.v_model in [".", ""] or selected.is_project() or selected.is_folder():
            return

        # open the delete dialog with the current file
        self.w_asset_dialog.reload(ee.Asset(selected))
        self.w_asset_dialog.value = True

    @switch("loading", "disabled", member="w_card")
    def on_new(self, *args):
        """Create a new folder cia the dialog."""
        # We need to be at least in a project to be able to create a new folder
        selected = self.w_selected.v_model
        if selected in [".", ""]:
            return

        self.w_create_dialog.reload(ee.Asset(self.folder))
        self.w_create_dialog.value = True

    def activate_buttons(self, change: dict):
        """Activate the appropriate buttons whenever the selected item changes."""
        # reset everything
        self.w_new.disabled = True
        self.w_view.disabled = True
        self.w_move.disabled = True
        self.w_delete.disabled = True
        self.w_copy.disabled = True
        self.w_copy.children[0].children = ["mdi-content-copy"]

        # We can activate the new button for projects
        asset = ee.Asset(change["new"])
        if asset.is_absolute():
            self.w_new.disabled = False

        # we need to exit if the selected item is a project or a root
        if change["new"] in [".", ""] or asset.is_project():
            return

        # reactivate delete move and copy for assets
        if asset.exists():
            self.w_delete.disabled = False
            self.w_move.disabled = False
            self.w_copy.disabled = False

            # we can only view files
            if not asset.is_folder():
                self.w_view.disabled = False


class DeleteAssetDialog(v.Dialog):
    """A dialog to confirm the deletion of an asset."""

    # -- Variables -------------------------------------------------------------

    asset: ee.Asset
    "The asset to delete"

    # -- Widgets ---------------------------------------------------------------
    w_confirm: v.Btn
    "The confirm button"

    w_cancel: v.Btn
    "The cancel button"

    def __init__(self, asset: Optional[ee.Asset] = None):
        """Initialize the class."""
        # start by defining all the widgets
        self.w_confirm = v.Btn(children=[v.Icon(children="mdi-check"), "Confirm"], color="primary")
        self.w_cancel = v.Btn(children=[v.Icon(children=["mdi-times"]), "Cancel"])
        w_title = v.CardTitle(children=["Delete the assets"])
        disclaimer = 'Clicking on "confirm" will definitively delete all the following asset. This action is definitive.'  # fmt: skip
        option = 'Click on "cancel" to abort the deletion.'

        self.ul = v.Html(tag="ul", children=[])
        w_content = v.CardText(children=[disclaimer, option, self.ul])

        w_actions = v.CardActions(children=[v.Spacer(), self.w_cancel, self.w_confirm])

        self.w_card = v.Card(children=[w_title, w_content, w_actions])

        super().__init__(children=[self.w_card], max_width="50%", persistent=True)

        # js interaction with the btns
        self.w_confirm.on_event("click", self.on_confirm)
        self.w_cancel.on_event("click", self.on_cancel)

    def reload(self, asset: ee.Asset):
        """Reload the dialog with a new asset."""
        # We should never arrive here with a non asset
        # but to avoid catastrophic destruction we will empty the list first
        if asset is None or str(asset) == ".":
            self.ul.children = []

        # save the asset as a member and read it
        self.asset = asset
        assets = asset.iterdir(recursive=True) if asset.is_folder() else [asset]
        self.ul.children = [v.Html(tag="li", children=[str(a)]) for a in assets]

    @switch("loading", "disabled", member="w_card")
    def on_confirm(self, *args):
        """Confirm the deletion."""
        # delete the asset and close the dialog
        if self.asset.is_folder():
            self.asset.rmdir(recursive=True, dry_run=False)
        else:
            self.asset.delete()
        self.value = False

    @switch("loading", "disabled", member="w_card")
    def on_cancel(self, *args):
        """Exit without doing anything."""
        self.value = False


class MoveAssetDialog(v.Dialog):
    """A dialog to confirm the move of an asset."""

    # -- Variables -------------------------------------------------------------

    asset: ee.Asset
    "The asset to delete"

    # -- Widgets ---------------------------------------------------------------
    w_asset: v.TextField
    "The destination to move"

    w_confirm: v.Btn
    "The confirm button"

    w_cancel: v.Btn
    "The cancel button"

    def __init__(self, asset: Optional[ee.Asset] = None):
        """Initialize the class."""
        # start by defining all the widgets
        # fmt: off
        self.w_asset = v.TextField(placeholder="Destination", v_model="", clearable=True, outlined=True, class_="ma-1")
        self.w_confirm = v.Btn(children=[v.Icon(children="mdi-check"), "Confirm"], color="primary")
        self.w_cancel = v.Btn(children=[v.Icon(children=["mdi-times"]), "Cancel"])
        w_title = v.CardTitle(children=["Delete the assets"])
        disclaimer = 'Clicking on "confirm" will move the following asset to the destination. This initial asset is not deleted.'
        option = 'Click on "cancel" to abort the move.'
        self.ul = v.Html(tag="ul", children=[])
        w_content = v.CardText(children=[self.w_asset, disclaimer, option, self.ul])
        w_actions = v.CardActions(children=[v.Spacer(), self.w_cancel, self.w_confirm])
        self.w_card = v.Card(children=[w_title, w_content, w_actions])
        # fmt: on

        super().__init__(children=[self.w_card], max_width="50%", persistent=True)

        # js interaction with the btns
        self.w_confirm.on_event("click", self.on_confirm)
        self.w_cancel.on_event("click", self.on_cancel)

    def reload(self, asset: ee.Asset):
        """Reload the dialog with a new asset."""
        # We should never arrive here with a non asset
        # but to avoid catastrophic destruction we will empty the list first
        if asset is None or str(asset) == ".":
            self.ul.children = []

        # save the asset as a member and read it
        self.asset = asset
        assets = asset.iterdir(recursive=True) if asset.is_folder() else [asset]
        self.ul.children = [v.Html(tag="li", children=[str(a)]) for a in assets]

    @switch("loading", "disabled", member="w_card")
    def on_confirm(self, *args):
        """Confirm the deletion."""
        # remove the warnings
        self.w_asset.error_messages = []

        # delete the asset and close the dialog
        try:
            self.asset.move(ee.Asset(self.w_asset.v_model))
            self.value = False
        except Exception as e:
            self.w_asset.error_messages = [str(e)]

    @switch("loading", "disabled", member="w_card")
    def on_cancel(self, *args):
        """Exit without doing anything."""
        self.value = False


class AssetDialog(v.Dialog):
    """A dialog to view an asset."""

    # -- Variables -------------------------------------------------------------

    asset: ee.Asset
    "The asset to delete"

    # -- Widgets ---------------------------------------------------------------

    w_exit: v.Btn
    "The exit button"

    def __init__(self, asset: Optional[ee.Asset] = None):
        """Initialize the class."""
        # start by defining all the widgets
        # fmt: off
        self.w_exit = v.Btn(children=[v.Icon(children="mdi-check"), "Exit"])
        self.w_title = v.CardTitle(children=["Delete the assets"])
        w_content = v.CardText(children=[""])
        w_actions = v.CardActions(children=[v.Spacer(), self.w_exit])
        self.w_card = v.Card(children=[self.w_title, w_content, w_actions])
        # fmt: on

        super().__init__(children=[self.w_card], max_width="50%", persistent=True)

        # js interaction with the btns
        self.w_exit.on_event("click", self.on_exit)

    def reload(self, asset: ee.Asset):
        """Reload the dialog with a new asset."""
        # We should never arrive here with a non asset
        # but to avoid catastrophic destruction we will empty the list first
        if asset is None or str(asset) == ".":
            self.ul.children = []

        # save the asset as a member and read it
        self.asset = asset
        self.w_title.children = [f"Viewing {asset.name}"]

    @switch("loading", "disabled", member="w_card")
    def on_exit(self, *args):
        """Exit without doing anything."""
        self.value = False


class CreateFolderDialog(v.Dialog):
    """A dialog to create a new folder asset."""

    # -- Variables -------------------------------------------------------------

    folder: ee.Asset
    "The current folder where to create the new folder."

    # -- Widgets ---------------------------------------------------------------
    w_asset: v.TextField
    "The destination to move"

    w_confirm: v.Btn
    "The confirm button"

    w_cancel: v.Btn
    "The cancel button"

    def __init__(self, asset: Optional[ee.Asset] = None):
        """Initialize the class."""
        # start by defining all the widgets
        # fmt: off
        self.w_asset = v.TextField(placeholder="Folder name", v_model="", clearable=True, outlined=True, class_="ma-1")
        self.w_confirm = v.Btn(children=[v.Icon(children="mdi-check"), "Confirm"], color="primary")
        self.w_cancel = v.Btn(children=[v.Icon(children=["mdi-times"]), "Cancel"])
        w_title = v.CardTitle(children=["Create a new folder"])
        w_content = v.CardText(children=[self.w_asset])
        w_actions = v.CardActions(children=[v.Spacer(), self.w_cancel, self.w_confirm])
        self.w_card = v.Card(children=[w_title, w_content, w_actions])
        # fmt: on

        super().__init__(children=[self.w_card], max_width="50%", persistent=True)

        # js interaction with the btns
        self.w_confirm.on_event("click", self.on_confirm)
        self.w_cancel.on_event("click", self.on_cancel)

    def reload(self, folder: ee.Asset):
        """Reload the dialog with a new asset."""
        # check the new destination is at least a project
        if not ee.Asset(folder).is_absolute():
            return

        self.folder = folder
        self.w_asset.prefix = f"{folder}/"
        self.w_asset.v_model = ""

    @switch("loading", "disabled", member="w_card")
    def on_confirm(self, *args):
        """Confirm the deletion."""
        # remove the warnings
        self.w_asset.error_messages = []

        # crezte the folder and close the dialog
        try:
            (self.folder / self.w_asset.v_model).mkdir(exist_ok=True, parents=True)
            self.value = False
        except Exception as e:
            self.w_asset.error_messages = [str(e)]

    @switch("loading", "disabled", member="w_card")
    def on_cancel(self, *args):
        """Exit without doing anything."""
        self.value = False
