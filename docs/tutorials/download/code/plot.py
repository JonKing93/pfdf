"Plotting code for the tutorials"

from math import nan

import cartopy.crs as ccrs
import fiona
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from pfdf.raster import Raster

####
# Utils
#####


def newplot(crs):
    "Creates a new figure for a CRS"
    projection = ccrs.epsg(crs.to_epsg())
    plt.close()
    plt.figure()
    ax = plt.axes(projection=projection)
    return ax


def finalize(ax, title, save, gridalpha=0):
    "Draw gridlines, adds titles, and optionally saves"
    ax.gridlines(draw_labels=["left", "bottom"], alpha=gridalpha)
    if title is not None:
        plt.title(title)
    if save:
        if isinstance(save, str):
            filename = save
        elif title is not None:
            filename = f"{title.lower().replace(' ','-')}.png"
        else:
            filename = "figure.png"
        plt.savefig(filename)


#####
# Basic Rasters
#####


def raster(raster, cmap, title=None, colorbar=True, ax=None, save=True, gridalpha=0):
    "Plots a raster"
    if ax is None:
        ax = newplot(raster.crs)

    values = raster.values.astype(float)
    values[raster.nodata_mask] = nan
    extent = [raster.left, raster.right, raster.bottom, raster.top]

    im = ax.imshow(values, extent=extent, cmap=cmap, interpolation="nearest")

    if colorbar:
        plt.colorbar(im)
    finalize(ax, title, save, gridalpha)


def mask(mask, title=None, ax=None, save=True, spatial=None, cmap=None, gridalpha=0):
    "Plots a raster mask"
    if spatial is not None:
        mask = Raster.from_array(mask, nodata=False, spatial=spatial)
    if cmap is None:
        cmap = mpl.colors.ListedColormap([0.5, 0.5, 0.5])
    raster(mask, cmap, title, colorbar=False, ax=ax, save=save, gridalpha=gridalpha)


def pr(perimeter, title=None, save=True):
    "Plots the retainment features against the perimeter"
    ax = newplot(perimeter.crs)
    mask(perimeter, ax=ax, save=False)
    retainments()
    finalize(ax, title, save)


#####
# Networks
#####


def retainments():
    "Adds retainment features to a map"
    with fiona.open("retainments.geojson") as collection:
        records = list(collection)
    for record in records:
        x, y = record.geometry.coordinates
        plt.plot(x, y, "ro")


def segment(line, color):
    "Plots a stream segment"
    x, y = line.xy
    plt.plot(x, y, color=color)


def lines(segments, color):
    "Plots multiple stream segments the same color"
    for line in segments.segments:
        segment(line, color)


def network(
    segments, title=None, perimeter=None, show_retainments=False, save=True, ax=None
):
    "Plots a stream segment network in one color"
    if ax is None:
        ax = newplot(segments.crs)
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False)
    if show_retainments:
        retainments()
    lines(segments, "b")
    finalize(ax, title, save)
    return ax


def filter(segments, keep, title=None, perimeter=None, save=True):
    "Plots retained segments in blue, and removable segments in red"
    keeping = segments.copy()
    keeping.keep(indices=keep, continuous=False)
    ax = network(keeping, perimeter=perimeter, show_retainments=False, save=False)

    remove = segments.copy()
    remove.remove(indices=keep, continuous=False)
    lines(remove, "r")

    finalize(ax, title, save)


def outlets(segments, title=None, save=True, show_segments=False, ax=None):
    "Plots the outlets as black circles"
    if ax is None:
        ax = newplot(segments.crs)
    if show_segments:
        network(segments, save=False, ax=ax)
    isterminus = segments.isterminus
    for k, line in enumerate(segments.segments):
        if isterminus[k]:
            x, y = line.xy
            x = x[-1]
            y = y[-1]
            plt.plot(x, y, "ko")
    finalize(ax, title, save)


def basins(
    segments,
    title=None,
    perimeter=None,
    save=True,
    show_segments=False,
    show_outlets=False,
):
    "Plots the basins as pink polygons"
    ax = newplot(segments.crs)
    if perimeter is not None:
        background = mpl.colors.ListedColormap(["white"])
        mask(perimeter, ax=ax, save=False, cmap=background)
    if show_segments:
        network(segments, save=False, ax=ax)
    if show_outlets:
        outlets(segments, save=False, ax=ax)
    basins = segments.geojson(type="basins")
    features = basins.features
    for feature in features:
        coords = feature.geometry.coordinates[0]
        coords = np.array(coords)
        poly = mpl.patches.Polygon(coords, facecolor="pink", edgecolor="black")
        ax.add_patch(poly)
    finalize(ax, title, save)


#####
# Model Results
#####


def probability(segments, probs, title=None, perimeter=None, save=True):
    "Plots the results of the probability model on the network"
    ax = newplot(segments.crs)
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False)

    cmap = mpl.colormaps["Reds"]
    colors = cmap(probs)
    for line, color in zip(segments.segments, colors):
        segment(line, color)

    norm = mpl.colors.Normalize(vmin=0, vmax=1)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    plt.colorbar(mapping, ax=ax)

    finalize(ax, title, save)


def volume(segments, volumes, title=None, perimeter=None, save=True):
    "Plots the volumes on the network"
    ax = newplot(segments.crs)
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False)

    cmap = mpl.colormaps["Reds"]
    norm = mpl.colors.LogNorm(vmin=1, vmax=1e5)
    cvals = norm(volumes)
    colors = cmap(cvals)

    for line, color in zip(segments.segments, colors):
        segment(line, color)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    plt.colorbar(mapping, ax=ax)
    finalize(ax, title, save)


def hazard(segments, hazard, title=None, perimeter=None, save=True):
    "Plots combined hazard class on the network"
    ax = newplot(segments.crs)
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False)

    cmap = mpl.colormaps["Reds"]
    norm = mpl.colors.Normalize(vmin=0, vmax=3)
    cvals = norm(hazard)
    colors = cmap(cvals)

    for line, color in zip(segments.segments, colors):
        segment(line, color)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    plt.colorbar(mapping, ax=ax)
    finalize(ax, title, save)
