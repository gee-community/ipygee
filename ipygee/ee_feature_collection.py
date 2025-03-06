"""Toolbox for the :py:class:`ee.FeatureCollection` class."""
from __future__ import annotations

import ee
import geetools  # noqa: F401
import numpy as np
from bokeh import plotting
from geetools.accessors import register_class_accessor
from matplotlib import pyplot as plt

from .plotting import plot_data


@register_class_accessor(ee.FeatureCollection, "bokeh")
class FeatureCollectionAccessor:
    """Toolbox for the :py:class:`ee.FeatureCollection` class."""

    def __init__(self, obj: ee.FeatureCollection):
        """Initialize the FeatureCollectionAccessor class."""
        self._obj = obj

    def plot_by_features(
        self,
        type: str = "bar",
        featureId: str = "system:index",
        properties: list[str] | None = None,
        labels: list[str] | None = None,
        colors: list[str] | None = None,
        figure: plotting.Figure | None = None,
        **kwargs,
    ) -> plotting.Figure:
        """Plot the values of a :py:class:`ee.FeatureCollection` by feature.

        Each feature property selected in properties will be plotted using the ``featureId`` as the x-axis.
        If no ``properties`` are provided, all properties will be plotted.
        If no ``featureId`` is provided, the ``"system:index"`` property will be used.

        Warning:
            This function is a client-side function.

        Args:
            type: The type of plot to use. Defaults to ``"bar"``. can be any type of plot from the python lib ``matplotlib.pyplot``. If the one you need is missing open an issue!
            featureId: The property to use as the x-axis (name the features). Defaults to ``"system:index"``.
            properties: A list of properties to plot. Defaults to all properties.
            labels: A list of labels to use for plotting the properties. If not provided, the default labels will be used. It needs to match the properties' length.
            colors: A list of colors to use for plotting the properties. If not provided, the default colors from the matplotlib library will be used.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            kwargs: Additional arguments from the ``pyplot`` type selected.

        See Also:
            - :docstring:`ee.FeatureCollection.geetools.byFeatures`
            - :docstring:`ee.FeatureCollection.geetools.plot_by_properties`
            - :docstring:`ee.FeatureCollection.geetools.plot_hist`
            - :docstring:`ee.FeatureCollection.geetools.plot`

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation
                from matplotlib import pyplot as plt

                initialize_documentation()

                # start a plot object from matplotlib library
                fig, ax = plt.subplots(figsize=(10, 5))

                # plot on this object the 10 first items of the FAO GAUL level 2 feature collection
                # for each one of them (marked with it's "ADM0_NAME" property) we plot the value of the "ADM1_CODE" and "ADM2_CODE" properties
                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                fc.geetools.plot_by_features(featureId="ADM2_NAME", properties=["ADM1_CODE", "ADM2_CODE"], colors=["#61A0D4", "#D49461"], ax=ax)

                # Modify the rotation of existing x-axis tick labels
                for label in ax.get_xticklabels():
                    label.set_rotation(45)
        """
        # Get the features and properties
        props = (
            ee.List(properties)
            if properties is not None
            else self._obj.first().propertyNames().getInfo()
        )
        props = props.remove(featureId)

        # get the data from server
        data = self._obj.geetools.byProperties(featureId, props, labels).getInfo()

        # reorder the data according to the labels or properties set by the user
        labels = labels if labels is not None else props.getInfo()
        data = {k: data[k] for k in labels}

        return plot_data(
            type=type, data=data, label_name=featureId, colors=colors, figure=figure, **kwargs
        )

    def plot_by_properties(
        self,
        type: str = "bar",
        featureId: str = "system:index",
        properties: list[str] | ee.List | None = None,
        labels: list[str] | None = None,
        colors: list[str] | None = None,
        figure: plotting.Feature | None = None,
        **kwargs,
    ) -> plotting.Feature:
        """Plot the values of a :py:class:`ee.FeatureCollection` by property.

        Each features will be represented by a color and each property will be a bar of the bar chart.

        Warning:
            This function is a client-side function.

        Args:
            type: The type of plot to use. Defaults to ``"bar"``. can be any type of plot from the python lib ``matplotlib.pyplot``. If the one you need is missing open an issue!
            featureId: The property to use as the y-axis (name the features). Defaults to ``"system:index"``.
            properties: A list of properties to plot. Defaults to all properties.
            labels: A list of labels to use for plotting the properties. If not provided, the default labels will be used. It needs to match the properties' length.
            colors: A list of colors to use for plotting the properties. If not provided, the default colors from the matplotlib library will be used.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            kwargs: Additional arguments from the ``pyplot`` function.

        Examples:
            .. jupyter-execute::

                import ee, ipygee
                from geetools.utils import initialize_documentation
                from matplotlib import pyplot as plt

                initialize_documentation()

                # start a plot object from matplotlib library
                fig, ax = plt.subplots(figsize=(10, 5))

                # plot on this object the 10 first items of the FAO GAUL level 2 feature collection
                # for each one of them (marked with it's "ADM2_NAME" property) we plot the value of the "ADM1_CODE" property
                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                fc.bokeh.plot_by_properties(featureId="ADM2_NAME", properties=["ADM1_CODE"], ax=ax)
        """
        # Get the features and properties
        fc = self._obj
        props = ee.List(properties) if properties is not None else fc.first().propertyNames()
        props = props.remove(featureId)

        # get the data from server
        data = self._obj.geetools.byFeatures(featureId, props, labels).getInfo()

        # reorder the data according to the lapbes or properties set by the user
        labels = labels if labels is not None else props.getInfo()
        data = {f: {k: data[f][k] for k in labels} for f in data.keys()}

        return plot_data(
            type=type, data=data, label_name=featureId, colors=colors, figure=figure, **kwargs
        )

    def plot_hist(
        self,
        property: str | ee.String,
        label: str = "",
        figure: plotting.Figure | None = None,
        color: str | None = None,
        **kwargs,
    ) -> plotting.Figure:
        """Plot the histogram of a specific property.

        Warning:
            This function is a client-side function.

        Args:
            property: The property to display
            label: The label to use for the property. If not provided, the property name will be used.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            color: The color to use for the plot. If not provided, the default colors from the matplotlib library will be used.
            **kwargs: Additional arguments from the :py:func:`matplotlib.pyplot.hist` function.

        Examples:
            .. jupyter-execute::

                import ee, ipygee
                from geetools.utils import initialize_documentation
                from matplotlib import pyplot as plt

                initialize_documentation()

                # start a plot object from matplotlib library
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.set_title('Histogram of Precipitation in July')
                ax.set_xlabel('Precipitation (mm)')


                # build the histogram of the precipitation band for the month of july in the PRISM dataset
                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm81m').toBands()
                region = ee.Geometry.Rectangle(-123.41, 40.43, -116.38, 45.14)
                climSamp = normClim.sample(region, 5000)
                climSamp.ipygee.plot_hist("07_ppt", ax=ax, bins=20)

                fig.show()
        """
        # gather the data from parameters
        properties, labels = ee.List([property]), ee.List([label])

        # get the data from the server
        data = self._obj.geetools.byProperties(properties=properties, labels=labels).getInfo()

        # create the graph objcet if not provided
        figure = plotting.figure() if figure is None else figure

        # gather the data from the data variable
        labels = list(data.keys())
        if len(labels) != 1:
            raise ValueError("histogram chart can only be used with one property")

        color = color or plt.get_cmap("tab10").colors[0]
        y, x = np.histogram(list(data[labels[0]].values()), **kwargs)
        figure.vbar(x=x, top=y, width=0.9, color=color)

        # customize the layout of the axis
        figure.xaxis.axis_label = labels[0]
        figure.yaxis.axis_label = "frequency"
        figure.xgrid.grid_line_color = None
        figure.outline_line_color = None

        return figure
