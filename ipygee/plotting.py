"""The extensive plotting function for bokhe binding."""
from __future__ import annotations

from datetime import datetime as dt
from math import pi

import numpy as np
from bokeh import plotting
from bokeh.layouts import column
from bokeh.models import RangeTool
from bokeh.models.layouts import Column
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex


def plot_data(
    type: str,
    data: dict,
    label_name: str,
    colors: list[str] | None = None,
    figure: plotting.figure | None = None,
    ax: plt.Axes | None = None,
    **kwargs,
) -> plotting.figure | Column:
    """Plotting mechanism used in all the plotting functions.

    It binds the bokeh capabilities with the data aggregated by different axes.
    the shape of the data should as follows:

    .. code-block::

        {
            "label1": {"properties1": value1, "properties2": value2, ...}
            "label2": {"properties1": value1, "properties2": value2, ...},
            ...
        }

    Args:
        type: The type of plot to use. can be any type of plot from the python lib `matplotlib.pyplot`. If the one you need is missing open an issue!
        data: the data to use as inputs of the graph. Please follow the format specified in the documentation.
        label_name: The name of the property that was used to generate the labels
        property_names: The list of names that was used to name the values. They will be used to order the keys of the data dictionary.
        colors: A list of colors to use for the plot. If not provided, the default colors from the matplotlib library will be used.
        figure: The bokeh figure to use. If not provided, the plot will be sent to a new figure.
        ax: The matplotlib axis to use. If not provided, the plot will be sent to a new axis.
        kwargs: Additional arguments from the ``figure`` chart type selected.

    Returns:
        The bokeh figure or the column of figure for time series.
    """
    # define the ax if not provided by the user
    figure = plotting.figure(match_aspect=True) if figure is None else figure

    # gather the data from parameters
    labels = list(data.keys())
    props = list(data[labels[0]].keys())
    colors = colors if colors else plt.get_cmap("tab10").colors

    # convert the colors to hexadecimal representation
    colors = [to_hex(c) for c in colors]

    # draw the chart based on the type
    if type == "plot":
        ticker_values = list(range(len(props)))
        for i, label in enumerate(labels):
            kwargs.update(color=colors[i], legend_label=label)
            figure.line(x=ticker_values, y=list(data[label].values()), **kwargs)
        figure.xaxis.ticker = ticker_values
        figure.xaxis.major_label_overrides = {i: p for i, p in enumerate(props)}
        figure.yaxis.axis_label = props[0] if len(props) == 1 else "Properties values"
        figure.xaxis.axis_label = f"Features (labeled by {label_name})"
        figure.xgrid.grid_line_color = None
        figure.outline_line_color = None
        return figure

    elif type == "scatter":
        ticker_values = list(range(len(props)))
        for i, label in enumerate(labels):
            kwargs.update(color=colors[i], legend_label=label)
            figure.scatter(x=ticker_values, y=list(data[label].values()), **kwargs)
        figure.xaxis.ticker = ticker_values
        figure.xaxis.major_label_overrides = {i: p for i, p in enumerate(props)}
        figure.yaxis.axis_label = props[0] if len(props) == 1 else "Properties values"
        figure.xaxis.axis_label = f"Features (labeled by {label_name})"
        figure.xgrid.grid_line_color = None
        figure.outline_line_color = None
        return figure

    elif type == "fill_between":
        ticker_values = list(range(len(props)))
        for i, label in enumerate(labels):
            values = list(data[label].values())
            bottom = [0] * len(values)
            kwargs.update(color=colors[i], legend_label=label)
            figure.varea(x=ticker_values, y1=bottom, y2=values, alpha=0.2, **kwargs)
            figure.line(x=ticker_values, y=values, **kwargs)
        figure.xaxis.ticker = ticker_values
        figure.xaxis.major_label_overrides = {i: p for i, p in enumerate(props)}
        figure.yaxis.axis_label = props[0] if len(props) == 1 else "Properties values"
        figure.xaxis.axis_label = f"Features (labeled by {label_name})"
        figure.xgrid.grid_line_color = None
        figure.outline_line_color = None
        return figure

    elif type == "bar":
        ticker_values = list(range(len(props)))
        data.update(props=ticker_values)

        x = np.arange(len(props))
        width = 1 / (len(labels) + 0.8)
        margin = width / 10
        ticks_value = x + width * len(labels) / 2
        figure.xaxis.ticker = ticks_value
        figure.xaxis.major_label_overrides = dict(zip(ticks_value, props))
        for i, label in enumerate(labels):
            values = list(data[label].values())
            kwargs.update(legend_label=label, color=colors[i])
            figure.vbar(x=x + width * i, top=values, width=width - margin, **kwargs)
        figure.xgrid.grid_line_color = None
        figure.outline_line_color = None
        return figure

    elif type == "barh":
        y = np.arange(len(props))
        height = 1 / (len(labels) + 0.8)
        margin = height / 10
        ticks_value = y + height * len(labels) / 2
        figure.yaxis.ticker = ticks_value
        figure.yaxis.major_label_overrides = dict(zip(ticks_value, props))
        for i, label in enumerate(labels):
            values = list(data[label].values())
            kwargs.update(legend_label=label, color=colors[i])
            figure.hbar(y=y + height * i, right=values, height=height - margin, **kwargs)
        figure.ygrid.grid_line_color = None
        figure.outline_line_color = None
        return figure

    elif type == "stacked":
        for label in labels:
            data[label] = [data[label][p] for p in props]
        ticker_values = list(range(len(props)))
        data.update(props=ticker_values)
        kwargs.update(color=colors, legend_label=labels, width=0.9)
        figure.vbar_stack(labels, x="props", source=data, **kwargs)
        figure.xaxis.ticker = ticker_values
        figure.xaxis.major_label_overrides = {i: p for i, p in enumerate(props)}
        figure.xgrid.grid_line_color = None
        return figure

    elif type == "pie":
        if len(labels) != 1:
            raise ValueError("Pie chart can only be used with one property")
        total = sum([data[labels[0]][p] for p in props])
        kwargs.update(x=0, y=0, radius=1)
        start_angle = 0
        for i, p in enumerate(props):
            kwargs.update(color=colors[i], legend_label=p)
            end_angle = start_angle + data[labels[0]][p] / total * 2 * pi
            figure.wedge(start_angle=start_angle, end_angle=end_angle, **kwargs)
            start_angle = end_angle
        figure.axis.visible = False
        figure.x_range.start, figure.y_range.start = -1.5, -1.5
        figure.x_range.end, figure.y_range.end = 1.5, 1.5
        figure.grid.grid_line_color = None
        figure.outline_line_color = None
        return figure

    elif type == "donut":
        if len(labels) != 1:
            raise ValueError("Pie chart can only be used with one property")
        total = sum([data[labels[0]][p] for p in props])
        kwargs.update(x=0, y=0, inner_radius=0.5, outer_radius=1)
        start_angle = 0
        for i, p in enumerate(props):
            kwargs.update(color=colors[i], legend_label=p)
            end_angle = start_angle + data[labels[0]][p] / total * 2 * pi
            figure.annular_wedge(start_angle=start_angle, end_angle=end_angle, **kwargs)
            start_angle = end_angle
        figure.axis.visible = False
        figure.x_range.start, figure.y_range.start = -1.5, -1.5
        figure.x_range.end, figure.y_range.end = 1.5, 1.5
        figure.grid.grid_line_color = None
        figure.outline_line_color = None
        return figure

    elif type == "date":
        # get the original height and width
        height, width = figure.height, figure.width

        # create the 2 figures that will be displayed in the column
        main = plotting.figure(
            height=int(height * 0.8), width=width, x_axis_type="datetime", x_axis_location="above"
        )
        main.outline_line_color = None

        # create the select item
        select = plotting.figure(
            height=int(height * 0.3),
            width=width,
            y_range=main.y_range,
            x_axis_type="datetime",
            y_axis_type=None,
            tools="",
        )
        select.title.text = "Drag the middle and edges of the selection box to change the range above"
        select.ygrid.grid_line_color = None
        select.outline_line_color = None

        # draw the curves on both figures
        for i, label in enumerate(labels):
            kwargs.update(color=colors[i], legend_label=label)
            x, y = list(data[label].keys()), list(data[label].values())
            main.line(x, y, color=colors[i], legend_label=label)
            select.line(x, y, color=colors[i])

        # add the range tool to the select figure
        range_tool = RangeTool(x_range=main.x_range)
        select.add_tools(range_tool)

        return column(main, select)

    elif type == "doy":
        xmin, xmax = 366, 0  # inverted initialization to get the first iteration values
        for i, label in enumerate(labels):
            x, y = list(data[label].keys()), list(data[label].values())
            figure.line(x, y, color=colors[i], legend_label=label)
            xmin, xmax = min(xmin, min(x)), max(xmax, max(x))
        dates = [dt(2023, i + 1, 1) for i in range(12)]
        idates = [int(d.strftime("%j")) - 1 for d in dates]
        ndates = [d.strftime("%B")[:3] for d in dates]
        figure.xaxis.ticker = idates
        figure.xaxis.major_label_overrides = dict(zip(idates, ndates))
        figure.xaxis.axis_label = "Day of year"
        figure.x_range.start = xmin - 5
        figure.x_range.end = xmax + 5
        return figure

    else:
        raise ValueError(f"Type {type} is not (yet?) supported")
