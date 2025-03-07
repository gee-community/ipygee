"""Toolbox for the :py:class:`ee.ImageCollection` class."""
from __future__ import annotations

from datetime import datetime as dt

import ee
import geetools  # noqa: F401
from bokeh import plotting
from geetools.accessors import register_class_accessor

from .plotting import plot_data

PY_DATE_FORMAT = "%Y-%m-%dT%H-%M-%S"
"The python format to use to parse dates coming from GEE."

EE_DATE_FORMAT = "YYYY-MM-dd'T'HH-mm-ss"
"The javascript format to use to burn date object in GEE."


@register_class_accessor(ee.ImageCollection, "bokeh")
class ImageCollectionAccessor:
    """Toolbox for the :py:class:`ee.ImageCollection` class."""

    def __init__(self, obj: ee.ImageCollection):
        """Initialize the ImageCollectionAccessor class."""
        self._obj = obj

    def plot_dates_by_bands(
        self,
        region: ee.Geometry,
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        bands: list[str] | None = None,
        labels: list[str] | None = None,
        colors: list[str] | None = None,
        figure: plotting.figure | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> plotting.figure:
        """Plot the reduced data for each image in the collection by bands on a specific region.

        This method is plotting the reduced data for each image in the collection by bands on a specific region.

        Parameters:
            region: The region to reduce the data on.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            bands: The bands to reduce. If empty, all bands are reduced.
            labels: The labels to use for the bands. If empty, the bands names are used.
            colors: The colors to use for the bands. If empty, the default colors are used.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A bokeh figure with the reduced values for each band and each date.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                region = ee.Geometry.Point(-122.262, 37.8719).buffer(10000)
                collection.geetools.plot_dates_by_bands(region, "mean", 10000, "system:time_start")
        """
        # get the reduced data
        raw_data = self._obj.geetools.datesByBands(
            region=region,
            reducer=reducer,
            dateProperty=dateProperty,
            bands=bands,
            labels=labels,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            bestEffort=bestEffort,
            maxPixels=maxPixels,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates int datetime objects
        def to_date(dict):
            return {dt.strptime(d, PY_DATE_FORMAT): v for d, v in dict.items()}

        data = {lbl: to_date(dict) for lbl, dict in raw_data.items()}

        # create the plot
        figure = plot_data(type="date", data=data, label_name="Date", colors=colors, figure=figure)

        return figure

    def plot_dates_by_regions(
        self,
        band: str,
        regions: ee.FeatureCollection,
        label: str = "system:index",
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        colors: list[str] | None = None,
        figure: plotting.figure | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> plotting.figure:
        """Plot the reduced data for each image in the collection by regions for a single band.

        This method is plotting the reduced data for each image in the collection by regions for a single band.

        Parameters:
            band: The band to reduce.
            regions: The regions to reduce the data on.
            label: The property to use as label for each region. Default is ``"system:index"``.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            colors: The colors to use for the regions. If empty, the default colors are used.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A bokeh figure with the reduced values for each region and each date.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                regions = ee.FeatureCollection([
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(10000), {"name": "region1"}),
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(20000), {"name": "region2"})
                ])

                collection.geetools.plot_dates_by_regions("B1", regions, "name", "mean", 10000, "system:time_start")
        """
        # get the reduced data
        raw_data = self._obj.geetools.datesByRegions(
            band=band,
            regions=regions,
            label=label,
            reducer=reducer,
            dateProperty=dateProperty,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates int datetime objects
        def to_date(dict):
            return {dt.strptime(d, PY_DATE_FORMAT): v for d, v in dict.items()}

        data = {lbl: to_date(dict) for lbl, dict in raw_data.items()}

        # create the plot
        figure = plot_data("date", data, "Date", colors, figure)

        return figure

    def plot_doy_by_bands(
        self,
        region: ee.Geometry,
        spatialReducer: str | ee.Reducer = "mean",
        timeReducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        bands: list[str] | None = None,
        labels: list[str] | None = None,
        colors: list[str] | None = None,
        figure: plotting.figure | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> plotting.figure:
        """Plot the reduced data for each image in the collection by bands on a specific region.

        This method is plotting the reduced data for each image in the collection by bands on a specific region.

        Parameters:
            region: The region to reduce the data on.
            spatialReducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            timeReducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            bands: The bands to reduce. If empty, all bands are reduced.
            labels: The labels to use for the bands. If empty, the bands names are used.
            colors: The colors to use for the bands. If empty, the default colors are used.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A bokeh figure with the reduced values for each band and each day.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                region = ee.Geometry.Point(-122.262, 37.8719).buffer(10000)
                collection.geetools.plot_doy_by_bands(region, "mean", "mean", 10000, "system:time_start")
        """
        # get the reduced data
        raw_data = self._obj.geetools.doyByBands(
            region=region,
            spatialReducer=spatialReducer,
            timeReducer=timeReducer,
            dateProperty=dateProperty,
            bands=bands,
            labels=labels,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            bestEffort=bestEffort,
            maxPixels=maxPixels,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates strings into int object and reorder the dictionary
        def to_int(d):
            return {int(k): v for k, v in d.items()}

        data = {lbl: dict(sorted(to_int(raw_data[lbl]).items())) for lbl in raw_data}

        # create the plot
        figure = plot_data("doy", data, "Day of Year", colors, figure)

        return figure

    def plot_doy_by_regions(
        self,
        band: str,
        regions: ee.FeatureCollection,
        label: str = "system:index",
        spatialReducer: str | ee.Reducer = "mean",
        timeReducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        colors: list[str] | None = None,
        figure: plotting.figure | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> plotting.figure:
        """Plot the reduced data for each image in the collection by regions for a single band.

        This method is plotting the reduced data for each image in the collection by regions for a single band.

        Parameters:
            band: The band to reduce.
            regions: The regions to reduce the data on.
            label: The property to use as label for each region. Default is ``"system:index"``.
            spatialReducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            timeReducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            colors: The colors to use for the regions. If empty, the default colors are used.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A bokeh figure with the reduced values for each region and each day.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                regions = ee.FeatureCollection([
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(10000), {"name": "region1"}),
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(20000), {"name": "region2"})
                ])

                collection.geetools.plot_doy_by_regions("B1", regions, "name", "mean", "mean", 10000, "system:time_start")
        """
        # get the reduced data
        raw_data = self._obj.geetools.doyByRegions(
            band=band,
            regions=regions,
            label=label,
            spatialReducer=spatialReducer,
            timeReducer=timeReducer,
            dateProperty=dateProperty,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates strings into int object and reorder the dictionary
        def to_int(d):
            return {int(k): v for k, v in d.items()}

        data = {lbl: dict(sorted(to_int(raw_data[lbl]).items())) for lbl in raw_data}

        # create the plot
        figure = plot_data("doy", data, "Day of Year", colors, figure)

        return figure

    def plot_doy_by_seasons(
        self,
        band: str,
        region: ee.Geometry,
        seasonStart: int | ee.Number = 1,
        seasonEnd: int | ee.Number = 366,
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        colors: list[str] | None = None,
        figure: plotting.figure | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> plotting.figure:
        """Plot the reduced data for each image in the collection by years for a single band.

        This method is plotting the reduced data for each image in the collection by years for a single band.
        To set the start and end of the season, use the :py:meth:`ee.Date.getRelative` or :py:class:`time.struct_time` method to get the day of the year.

        Parameters:
            band: The band to reduce.
            region: The region to reduce the data on.
            seasonStart: The day of the year that marks the start of the season.
            seasonEnd: The day of the year that marks the end of the season.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            colors: The colors to use for the regions. If empty, the default colors are used.
            figure: The bokeh figure to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A bokeh figure with the reduced values for each year and each day.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filter(ee.Filter.Or(
                        ee.Filter.date("2022-01-01", "2022-12-31"),
                        ee.Filter.date("2016-01-01", "2016-12-31"),
                    ))
                    .map(lambda i: ee.Image(i).addBands(
                        ee.Image(i)
                        .normalizedDifference(["B5", "B4"])
                        .rename("NDVI")
                    ))
                )

                collection.geetools.plot_doy_by_seasons(
                    band = "NDVI",
                    region = ee.Geometry.Point(-122.262, 37.8719).buffer(1000),
                    seasonStart = ee.Date("2016-05-01").getRelative("day", "year"),
                    seasonEnd = ee.Date("2016-10-31").getRelative("day", "year"),
                    reducer = "mean",
                    dateProperty = "system:time_start",
                    scale = 10000
                )
        """
        # get the reduced data
        raw_data = self._obj.geetools.doyBySeasons(
            band=band,
            region=region,
            seasonStart=seasonStart,
            seasonEnd=seasonEnd,
            reducer=reducer,
            dateProperty=dateProperty,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            bestEffort=bestEffort,
            maxPixels=maxPixels,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates strings into int object and reorder the dictionary
        def to_int(d):
            return {int(k): v for k, v in d.items()}

        data = {lbl: dict(sorted(to_int(raw_data[lbl]).items())) for lbl in raw_data}

        # create the plot
        figure = plot_data("doy", data, "Day of Year", colors, figure)

        return figure
