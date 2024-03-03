"""he task manager widget and functionalitites."""
from __future__ import annotations

from datetime import datetime as dt
from pathlib import Path
from typing import List

import ee
import ipyvuetify as v

from .decorator import switch

ICON_TYPE = {
    "EXPORT_IMAGE": "mdi-image-outline",
    "EXPORT_FEATURES": "mdi-table",
}

ICON_STATUS = {
    "RUNNING": ["mdi-cog", "primary"],
    "SUCCEEDED": ["mdi-check", "success"],
    "FAILED": ["mdi-alert", "error"],
}

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class TaskManager(v.Flex):
    """A task manager widget."""

    # -- Widgets ---------------------------------------------------------------

    w_reload: v.Btn
    "The reload btn at the top of the Task manager"

    w_search: v.Btn
    "The search button to crowl into the existing tasks"

    w_list: v.List
    "The list of tasks displayed in the Task manager"

    w_card: v.Card
    "The card hosting the list of tasks"

    def __init__(self):
        """Initialize the widget."""
        # start by defining al the widgets
        # We deactivated the formatting to define each one of them on 1 single line
        # fmt: off


        # add a line of buttons to reload and saerch items
        self.w_reload = v.Btn(children=[v.Icon(color="primary", children="mdi-reload")], elevation=2, class_="ma-1")
        self.w_search = v.Btn(children=[v.Icon(color="primary", children="mdi-magnify")], elevation=2, class_="ma-1")
        w_main_line = v.Flex(children=[self.w_reload, self.w_search])

        # generate the list of tasks
        w_group = v.ListItemGroup(children=self.get_tasks(), v_model="")
        self.w_list = v.List(dense=True, v_model=True, children=[w_group], outlined=True)
        self.w_card = v.Card(children=[self.w_list], class_="ma-1", elevation=0)

        super().__init__(children=[w_main_line, self.w_card], v_model="", class_="ma-1")
        # fmt: on

        # javascrit interaction
        self.w_reload.on_event("click", self.on_reload)

    def get_tasks(self) -> List[v.ListItem]:
        """Create the list of tasks from the current user."""
        # get all the tasks
        tasks = ee.data.listOperations()

        # build the listItems from the information
        task_list = []
        for t in tasks:

            # build a dictionary of metadata for the expansion panel
            state = t["metadata"]["state"]
            metadata = {
                "id": Path(t["name"]).name,
                "phase": state,
                "attempted": f"{t['metadata']['attempt']} time",
            }

            # add time information if the task computed
            if state in ["SUCCEEDED", "FAILED"]:
                start = dt.strptime(t["metadata"]["startTime"], DATE_FORMAT)
                end = dt.strptime(t["metadata"]["endTime"], DATE_FORMAT)
                runtime = (end - start).seconds
                hours, r = divmod(runtime, 3600)
                minutes, seconds = divmod(r, 60)
                metadata.update(runtime=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # add EECCU consumption if the task was a success
            if state == "SUCCEEDED":
                metadata.update(consumption=f"{t['metadata']['batchEecuUsageSeconds']:4f} EECU/s")

            # display the information in a list
            ul_content = []
            for k, m in metadata.items():
                title = v.Html(tag="b", children=[f"{k}: "])
                text = v.Html(tag="span", children=[m])
                ul_content.append(v.Html(tag="li", children=[title, text]))
            content_list = v.Html(tag="ul", children=ul_content, style_="list-style-type: none")

            # the header will include multiple information from the task:
            # status, type of output and name
            icon, color = ICON_STATUS[state]
            w_status = v.Icon(children=[icon], color=color, class_="mr-1")
            w_type = v.Icon(children=[ICON_TYPE[t["metadata"]["type"]]], class_="mr-1")
            name = t["metadata"]["description"]
            header_row = v.Flex(children=[w_status, w_type, name])

            # finally we build each individual expansion panels
            content = v.ExpansionPanelContent(children=[content_list])
            header = v.ExpansionPanelHeader(children=[header_row])
            expansion_panel = v.ExpansionPanel(children=[header, content])

            task_list.append(v.ExpansionPanels(children=[expansion_panel], class_="pa-1"))

        return task_list

    @switch("loading", "disabled", member="w_card")
    def on_reload(self, *args):
        """Reload the list of tasks."""
        self.w_list.children = [v.ListItemGroup(children=self.get_tasks(), v_model="")]
