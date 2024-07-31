"Plotting code for the tutorials"

from math import nan

import cartopy.crs as ccrs
import fiona
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from pfdf.raster import Raster
from pyproj.transformer import Transformer

CRS = 26911

####
# Utils
#####


def newplot():
    "Creates a new figure in the default CRS"
    projection = ccrs.epsg(CRS)
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
        ax = newplot()

    raster = raster.copy()
    raster.reproject(crs=CRS)
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
    ax = newplot()
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
        crs = collection.crs
    transformer = Transformer.from_crs(crs, CRS, always_xy=True)
    for record in records:
        x, y = record.geometry.coordinates
        x, y = transformer.transform(x, y)
        plt.plot(x, y, "ro")


def segment(line, color, transformer):
    "Plots a stream segment"
    x, y = line.xy
    x, y = transformer.transform(x, y)
    plt.plot(x, y, color=color)


def lines_fixed_color(segments, color):
    "Plots multiple stream segments the same color"
    transformer = Transformer.from_crs(segments.crs, CRS, always_xy=True)
    for line in segments.segments:
        segment(line, color, transformer)


def network(
    segments, title=None, perimeter=None, show_retainments=False, save=True, ax=None
):
    "Plots a stream segment network in one color"
    if ax is None:
        ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False)
    if show_retainments:
        retainments()
    lines_fixed_color(segments, "b")
    finalize(ax, title, save)
    return ax


def filter(segments, keep, title=None, perimeter=None, save=True):
    "Plots retained segments in blue, and removable segments in red"
    keeping = segments.copy()
    keeping.keep(keep)
    ax = network(keeping, perimeter=perimeter, show_retainments=False, save=False)

    remove = segments.copy()
    remove.remove(keep)
    lines_fixed_color(remove, "r")

    finalize(ax, title, save)


def outlets(segments, title=None, save=True, show_segments=False, ax=None):
    "Plots the outlets as black circles"
    if ax is None:
        ax = newplot()
    if show_segments:
        network(segments, save=False, ax=ax)
    isterminus = segments.isterminal()
    transformer = Transformer.from_crs(segments.crs, CRS, always_xy=True)
    for k, line in enumerate(segments.segments):
        if isterminus[k]:
            x, y = line.xy
            x = x[-1]
            y = y[-1]
            x, y = transformer.transform(x, y)
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
    ax = newplot()
    if perimeter is not None:
        background = mpl.colors.ListedColormap(["white"])
        mask(perimeter, ax=ax, save=False, cmap=background)
    if show_segments:
        network(segments, save=False, ax=ax)
    if show_outlets:
        outlets(segments, save=False, ax=ax)

    basins = segments.geojson(type="basins")
    features = basins.features
    transformer = Transformer.from_crs(segments.crs, CRS, always_xy=True)

    for feature in features:
        coords = feature.geometry.coordinates[0]
        coords = np.array(coords)
        xs = coords[:, 0]
        ys = coords[:, 1]
        xs, ys = transformer.transform(xs, ys)
        coords = np.stack((xs, ys), -1)
        poly = mpl.patches.Polygon(coords, facecolor="pink", edgecolor="black")
        ax.add_patch(poly)
    finalize(ax, title, save)


#####
# Model Results
#####


def likelihood(segments, probs, title=None, perimeter=None, save=True):
    "Plots the results of the likelihood model on the network"
    ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False)

    cmap = mpl.colormaps["Reds"]
    colors = cmap(probs)
    transformer = Transformer.from_crs(segments.crs, CRS, always_xy=True)
    for line, color in zip(segments.segments, colors):
        segment(line, color, transformer)

    norm = mpl.colors.Normalize(vmin=0, vmax=1)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    plt.colorbar(mapping, ax=ax)

    finalize(ax, title, save)


def volume(segments, volumes, title=None, perimeter=None, save=True):
    "Plots the volumes on the network"
    ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False)

    cmap = mpl.colormaps["Reds"]
    norm = mpl.colors.LogNorm(vmin=1, vmax=1e5)
    cvals = norm(volumes)
    colors = cmap(cvals)

    transformer = Transformer.from_crs(segments.crs, CRS, always_xy=True)
    for line, color in zip(segments.segments, colors):
        segment(line, color, transformer)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    plt.colorbar(mapping, ax=ax)
    finalize(ax, title, save)


def hazard(segments, hazard, title=None, perimeter=None, save=True):
    "Plots combined hazard class on the network"
    ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False)

    cmap = mpl.colormaps["Reds"]
    norm = mpl.colors.Normalize(vmin=0, vmax=3)
    cvals = norm(hazard)
    colors = cmap(cvals)

    transformer = Transformer.from_crs(segments.crs, CRS, always_xy=True)
    for line, color in zip(segments.segments, colors):
        segment(line, color, transformer)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    plt.colorbar(mapping, ax=ax)
    finalize(ax, title, save)


def thresholds(segments, thresholds, title=None, perimeter=None, save=True):
    "Plots rainfall thresholds"

    ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False)

    cmap = mpl.colormaps["Reds_r"]
    norm = mpl.colors.Normalize(vmin=0, vmax=60)
    cvals = norm(thresholds)
    colors = cmap(cvals)

    transformer = Transformer.from_crs(segments.crs, CRS, always_xy=True)
    for line, color in zip(segments.segments, colors):
        segment(line, color, transformer)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    plt.colorbar(mapping, ax=ax)
    finalize(ax, title, save)
