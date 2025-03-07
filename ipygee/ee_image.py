"""Toolbox for the :py:class:`ee.Image` class."""
from __future__ import annotations

import ee
import geetools  # noqa: F401
from bokeh import plotting
from geetools.accessors import register_class_accessor
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex

from .plotting import plot_data


@register_class_accessor(ee.Image, "bokeh")
class ImageAccessor:
    """Toolbox for the :py:class:`ee.Image` class."""

    def __init__(self, obj: ee.Image):
        """Initialize the Image class."""
        self._obj = obj

    def plot_by_regions(
        self,
        type: str,
        regions: ee.FeatureCollection,
        reducer: str | ee.Reducer = "mean",
        bands: list[str] | None = None,
        regionId: str = "system:index",
        labels: list[str] | None = None,
        colors: list[str] | None = None,
        figure: plotting.figure | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> plotting.figure:
        """Plot the reduced values for each region.

        Each region will be plotted using the ``regionId`` as x-axis label defaulting to "system:index" if not provided.
        If no ``bands`` are provided, all bands will be plotted.
        If no ``labels`` are provided, the band names will be used.

        Warning:
            This method is client-side.

        Parameters:
            type: The type of plot to use. Defaults to ``"bar"``. can be any type of plot from the python lib ``matplotlib.pyplot``. If the one you need is missing open an issue!
            regions: The regions to compute the reducer in.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            bands: The bands to compute the reducer on. Default to all bands.
            regionId: The property used to label region. Defaults to ``"system:index"``.
            labels: The labels to use for the output dictionary. Default to the band names.
            colors: The colors to use for the plot. Default to the default matplotlib colors.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            scale: The scale to use for the computation. Default is 10000m.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            The bokeh figure with the plot.

        Examples:
            .. code-block:: python

                import ee, ipygee

                ee.Initialize()

                ecoregions = ee.FeatureCollection("projects/google/charts_feature_example").select(["label", "value","warm"])
                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm91m').toBands()

                normClim.bokeh.plot_by_regions(ecoregions, ee.Reducer.mean(), scale=10000)
        """
        # get the data from the server
        data = self._obj.geetools.byBands(
            regions=regions,
            reducer=reducer,
            bands=bands,
            regionId=regionId,
            labels=labels,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        ).getInfo()

        # get all the id values, they must be string so we are forced to cast them manually
        # the default casting is broken from Python side: https://issuetracker.google.com/issues/329106322
        features = regions.aggregate_array(regionId)
        isString = lambda i: ee.Algorithms.ObjectType(i).compareTo("String").eq(0)  # noqa: E731
        features = features.map(lambda i: ee.Algorithms.If(isString(i), i, ee.Number(i).format()))
        features = features.getInfo()

        # extract the labels from the parameters
        eeBands = ee.List(bands) if bands is not None else self._obj.bandNames()
        labels = labels if labels is not None else eeBands.getInfo()

        # reorder the data according to the labels id set by the user
        data = {b: {f: data[b][f] for f in features} for b in labels}

        ax = plot_data(type=type, data=data, label_name=regionId, colors=colors, figure=figure)

        return ax

    def plot_by_bands(
        self,
        type: str,
        regions: ee.FeatureCollection,
        reducer: str | ee.Reducer = "mean",
        bands: list[str] | None = None,
        regionId: str = "system:index",
        labels: list[str] | None = None,
        colors: list[str] | None = None,
        figure: plotting.figure | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> plotting.figure:
        """Plot the reduced values for each band.

        Each band will be plotted using the ``labels`` as x-axis label defaulting to band names if not provided.
        If no ``bands`` are provided, all bands will be plotted.
        If no ``regionId`` are provided, the ``"system:index"`` property will be used.

        Warning:
            This method is client-side.

        Parameters:
            type: The type of plot to use. Defaults to ``"bar"``. can be any type of plot from the python lib ``matplotlib.pyplot``. If the one you need is missing open an issue!
            regions: The regions to compute the reducer in.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            bands: The bands to compute the reducer on. Default to all bands.
            regionId: The property used to label region. Defaults to ``"system:index"``.
            labels: The labels to use for the output dictionary. Default to the band names.
            colors: The colors to use for the plot. Default to the default matplotlib colors.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            scale: The scale to use for the computation. Default is 10000m.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            The bokeh figure with the plot

        Examples:
            .. code-block:: python

                import ee, ipygee

                ee.Initialize()

                ecoregions = ee.FeatureCollection("projects/google/charts_feature_example").select(["label", "value","warm"])
                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm91m').toBands()

                normClim.bokeh.plot_by_bands(ecoregions, ee.Reducer.mean(), scale=10000)
        """
        # get the data from the server
        data = self._obj.geetools.byRegions(
            regions=regions,
            reducer=reducer,
            bands=bands,
            regionId=regionId,
            labels=labels,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        ).getInfo()

        # get all the id values, they must be string so we are forced to cast them manually
        # the default casting is broken from Python side: https://issuetracker.google.com/issues/329106322
        features = regions.aggregate_array(regionId)
        isString = lambda i: ee.Algorithms.ObjectType(i).compareTo("String").eq(0)  # noqa: E731
        features = features.map(lambda i: ee.Algorithms.If(isString(i), i, ee.Number(i).format()))
        features = features.getInfo()

        # extract the labels from the parameters
        eeBands = ee.List(bands) if bands is not None else self._obj.bandNames()
        labels = labels if labels is not None else eeBands.getInfo()

        # reorder the data according to the labels id set by the user
        data = {f: {b: data[f][b] for b in labels} for f in features}

        ax = plot_data(type=type, data=data, label_name=regionId, colors=colors, figure=figure)

        return ax

    def plot_hist(
        self,
        bins: int = 30,
        region: ee.Geometry | None = None,
        bands: list[str] | None = None,
        labels: list[str] | None = None,
        colors: list[str] | None = None,
        precision: int = 2,
        figure: plotting.figure | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int = 10**7,
        tileScale: float = 1,
        **kwargs,
    ) -> plotting.figure:
        """Plot the histogram of the image bands.

        Parameters:
            bins: The number of bins to use for the histogram. Default is 30.
            region: The region to compute the histogram in. Default is the image geometry.
            bands: The bands to plot the histogram for. Default to all bands.
            labels: The labels to use for the output dictionary. Default to the band names.
            colors: The colors to use for the plot. Default to the default matplotlib colors.
            precision: The number of decimal to keep for the histogram bins values. Default is 2.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            scale: The scale to use for the computation. Default is 10,000m.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. default to 10**7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.
            **kwargs: Keyword arguments passed to the `matplotlib.fill_between() <https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.fill_between.html>`_ function.

        Returns:
            The bokeh figure with the plot.

        Examples:
            .. code-block:: python

                import ee, ipygee

                ee.Initialize()

                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm91m').toBands()
                normClim.bokeh.plot_hist()
        """
        # extract the bands from the image
        eeBands = ee.List(bands) if bands is not None else self._obj.bandNames()
        eeLabels = ee.List(labels).flatten() if labels is not None else eeBands
        new_labels: list[str] = eeLabels.getInfo()
        new_colors: list[str] = colors if colors is not None else plt.get_cmap("tab10").colors

        # retrieve the region from the parameters
        region = region if region is not None else self._obj.geometry()

        # extract the data from the server
        image = self._obj.select(eeBands).rename(eeLabels).clip(region)

        # set the common parameters of the 3 reducers
        params = {
            "geometry": region,
            "scale": scale,
            "crs": crs,
            "crsTransform": crsTransform,
            "bestEffort": bestEffort,
            "maxPixels": maxPixels,
            "tileScale": tileScale,
        }

        # compute the min and max values of the bands so w can scale the bins of the histogram
        min = image.reduceRegion(**{"reducer": ee.Reducer.min(), **params})
        min = min.values().reduce(ee.Reducer.min())

        max = image.reduceRegion(**{"reducer": ee.Reducer.max(), **params})
        max = max.values().reduce(ee.Reducer.max())

        # compute the histogram. The result is a dictionary with each band as key and the histogram
        # as values. The histograp is a list of [start of bin, value] pairs
        reducer = ee.Reducer.fixedHistogram(min, max, bins)
        raw_data = image.reduceRegion(**{"reducer": reducer, **params}).getInfo()

        # massage raw data to reshape them as usable source for an Axes plot
        # first extract the x coordinates of the plot as a list of bins borders
        # every value is duplicated but the first one to create a scale like display.
        # the values are treated the same way we simply drop the last duplication to get the same size.
        p = 10**precision  # multiplier use to truncate the float values
        x = [int(d[0] * p) / p for d in raw_data[new_labels[0]] for _ in range(2)][1:]
        data = {lbl: [int(d[1]) for d in raw_data[lbl] for _ in range(2)][:-1] for lbl in new_labels}

        # create the graph objcet if not provided
        figure = plotting.figure() if figure is None else figure

        # display the histogram as a fill_between plot to respect GEE lib design
        for i, label in enumerate(new_labels):
            y = data[label]
            bottom = [0] * len(data[label])
            color = to_hex(new_colors[i])
            figure.varea(x=x, y1=bottom, y2=y, legend_label=label, color=color, alpha=0.2, **kwargs)
            figure.line(x=x, y=y, legend_label=label, color=color)

        # customize the layout of the axis
        figure.yaxis.axis_label = "Count"
        figure.xgrid.grid_line_color = None
        figure.outline_line_color = None

        return figure
