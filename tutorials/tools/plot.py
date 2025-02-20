import cartopy.crs as ccrs
import contextily as cx
import fiona
import fiona.transform
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from numpy import nan
from pyproj import CRS

from pfdf.raster import Raster

from .workspace import workspace


def initialize():
    "Initializes a plot. Returns the axis and CRS"

    crs = CRS(3857)
    projection = ccrs.epsg(crs.to_epsg())
    plt.figure()
    ax = plt.axes(projection=projection)
    return ax, crs


def label(ax, title):
    "Adds title and coordinate ticks"
    plt.title(title)
    ax.gridlines(draw_labels=["left", "bottom"], alpha=0)


def raster(raster, cmap, title, clabel=None, show_basemap: bool = False):
    "Plots a raster dataset"

    # Initialize plot and get CRS
    ax, crs = initialize()

    # Reproject the raster into the map projection
    raster = raster.copy()
    raster.reproject(crs=crs)

    # Replace NoData values with NaN to remove them from plots
    values = raster.values.astype(float, copy=True)
    values[raster.nodata_mask] = nan

    # Set the figure extent
    bounds = raster.bounds
    ax.set_xlim(bounds.xs)
    ax.set_ylim(bounds.ys)

    # Optionally add a base map
    if show_basemap:
        cx.add_basemap(ax)

    # Plot the raster
    extent = bounds.xs + bounds.ys
    im = ax.imshow(values, extent=extent, cmap=cmap, interpolation="nearest")

    # Label the plot
    label(ax, title)
    plt.colorbar(im, label=clabel)


def mask(mask, title, legend=None, spatial=None, basemap: bool = True):
    "Plots a raster mask"

    # Initialize plot and get CRS
    ax, crs = initialize()

    # Convert numpy mask to Raster
    if spatial is not None:
        mask = Raster.from_array(mask, spatial=spatial, isbool=True)

    # Reproject the mask into the map projection
    mask = mask.copy()
    mask.reproject(crs=crs)

    # Replace NoData with NaN
    values = mask.values.astype(float)
    values[mask.nodata_mask] = nan

    # Set the figure extent
    bounds = mask.bounds
    ax.set_xlim(bounds.xs)
    ax.set_ylim(bounds.ys)

    # Add base map
    if basemap:
        cx.add_basemap(ax)

    # Plot the mask
    extent = bounds.xs + bounds.ys
    color = [0.5, 0.5, 0.5]
    cmap = ListedColormap(color)
    ax.imshow(values, extent=extent, cmap=cmap, interpolation="nearest")

    # Label the plot
    label(ax, title)
    if legend is None:
        legend = title
    mask = mpl.patches.Patch(color=color, label=legend)
    plt.legend(handles=[mask], loc='upper left')


def load_retainments(path, crs):

    # Load the retainment dataset
    with fiona.open(path, layer="DebrisBasin") as file:
        icrs = file.crs
        points = [feature["geometry"] for feature in list(file)]

    # Reproject to match the map CRS
    for p, point in enumerate(points):
        point = fiona.transform.transform_geom(
            src_crs=icrs,
            dst_crs=crs,
            geom=point,
        )
        points[p] = point
    return points


def retainments(path, title, perimeter=None):
    "Plots debris retainment features"

    # Initialize plot and get CRS
    ax, crs = initialize()

    # Load the dataset
    points = load_retainments(path, crs)

    # Optionally prepare the fire perimeter as well
    if perimeter is not None:
        perimeter = perimeter.copy()
        perimeter.reproject(crs=crs)
        values = perimeter.values.astype(float)
        values[perimeter.nodata_mask] = nan

    # Plot the retainments
    coords = [point["coordinates"] for point in points]
    coords = np.array(coords)
    plt.scatter(x=coords[:, 0], y=coords[:, 1], c="red", marker="^")

    # Add basemap
    cx.add_basemap(ax)

    # Optionally add the perimeter
    if perimeter is not None:
        bounds = perimeter.bounds
        extent = bounds.xs + bounds.ys
        cmap = ListedColormap([0.5, 0.5, 0.5])
        ax.imshow(values, extent=extent, cmap=cmap, interpolation="nearest")

    # Label the plot
    label(ax, title)


def get_coords(segments, crs, geometry="segments"):
    "Extracts feature coordinates from a collection"
    features = segments.geojson(geometry, crs=crs)["features"]
    return [feature["geometry"]["coordinates"] for feature in features]


def network(
    segments,
    title,
    perimeter=None,
    keep=None,
    show_retainments: bool = False,
    show_basins: bool = False,
    show_outlets: bool = False,
):

    # Initialize plot. Get CRS. Set bounds
    ax, crs = initialize()
    bounds = segments.bounds.reproject(crs)
    ax.set_xlim(bounds.xs)
    ax.set_ylim(bounds.ys)

    # Keep all segments unless otherwise noted
    if keep is None:
        keep = np.ones(segments.size, bool)

    # Load the retainments
    if show_retainments:
        path = workspace() / "data" / "la-county-retainments.gdb"
        points = load_retainments(path, crs=crs)

    # Prepare the fire perimeter
    if perimeter is not None:
        perimeter = Raster.from_array(perimeter, spatial=segments.flow, isbool=True)
        perimeter.reproject(crs=crs)
        values = perimeter.values.astype(float)
        values[perimeter.nodata_mask] = nan

    # Optionally plot the basins
    if show_basins:
        coords = get_coords(segments, crs, "basins")
        for polygon in coords:
            basin = np.array(polygon[0])
            basin = mpl.patches.Polygon(basin, facecolor="pink", edgecolor="black")
            ax.add_patch(basin)

    # Plot the segments
    coords = get_coords(segments, crs)
    for line, keep in zip(coords, keep):
        line = np.array(line)
        xs = line[:, 0]
        ys = line[:, 1]
        if keep:
            color = "blue"
        else:
            color = "red"
        plt.plot(xs, ys, color=color)

    # Optionally add the outlets
    if show_outlets:
        coords = get_coords(segments, crs, "outlets")
        for x, y in coords:
            plt.plot(x, y, "ko")

    # Add the retainments
    if show_retainments:
        coords = [point["coordinates"] for point in points]
        coords = np.array(coords)
        plt.scatter(x=coords[:, 0], y=coords[:, 1], c="red", marker="^")

    # Add basemap
    cx.add_basemap(ax)

    # Optionally add the perimeter
    if perimeter is not None:
        bounds = perimeter.bounds
        extent = bounds.xs + bounds.ys
        cmap = ListedColormap([0.5, 0.5, 0.5])
        ax.imshow(values, extent=extent, cmap=cmap, interpolation="nearest")

    # Label the plot
    label(ax, title)


def _results(segments, colors, title, cmapping, clabel=None):
    "Plots hazard modeling results"

    # Initialize plot. Get CRS and set bounds
    ax, crs = initialize()
    bounds = segments.bounds.reproject(crs)
    ax.set_xlim(bounds.xs)
    ax.set_ylim(bounds.ys)

    # Get the segment geometries
    features = segments.geojson(crs=crs)["features"]
    coords = [feature["geometry"]["coordinates"] for feature in features]

    # Plot the segments
    for line, color in zip(coords, colors):
        line = np.array(line)
        xs = line[:, 0]
        ys = line[:, 1]
        plt.plot(xs, ys, color=color)

    # Add basemap
    cx.add_basemap(ax)

    # Label
    label(ax, title)
    plt.colorbar(cmapping, ax=ax, label=clabel)


def I15_title(title, I15):
    return f"{title}\n(I15 = {I15} mm/hr)"


def volumes(segments, V, title, I15, clabel):
    "Plots potential sediment volume results"

    # Build the colormap
    cmap = mpl.colormaps["Reds"]
    norm = mpl.colors.LogNorm(vmin=1, vmax=1e5)
    cvals = norm(V)
    colors = cmap(cvals)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

    # Plot results
    title = I15_title(title, I15)
    _results(segments, colors, title, mapping, clabel=clabel)


def likelihood(segments, P, title, I15, clabel):
    "Plots debris-flow likelihood results"

    # Get the colormap
    cmap = mpl.colormaps["Reds"]
    colors = cmap(P)
    norm = mpl.colors.Normalize(vmin=0, vmax=1)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

    # Plot
    title = I15_title(title, I15)
    _results(segments, colors, title, mapping, clabel)


def hazard(segments, H, title, I15, clabel):
    "Plots hazard classification results"

    # Build colormap
    cmap = mpl.colormaps["Reds"]
    norm = mpl.colors.Normalize(vmin=0, vmax=3)
    cvals = norm(H)
    colors = cmap(cvals)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

    # Plot
    title = I15_title(title, I15)
    _results(segments, colors, title, mapping, clabel)


def thresholds(segments, R, title, I15, p, clabel):
    "Plots rainfall threshold results"

    # Build colormap
    cmap = mpl.colormaps["Reds_r"]
    norm = mpl.colors.Normalize(vmin=0, vmax=40)
    cvals = norm(R)
    colors = cmap(cvals)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

    # Plot
    title = f"{title}\n(I15 = {I15} mm/hr, p = {int(100*p)}%)"
    _results(segments, colors, title, mapping, clabel)
