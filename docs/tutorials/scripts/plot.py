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

    # Add gridlines and title
    ax.gridlines(draw_labels=["left", "bottom"], alpha=gridalpha)
    if title is not None:
        plt.title(title)

    # Save to file
    if save:
        if isinstance(save, str):
            filename = save
        elif title is not None:
            filename = f"{title.lower().replace(' ','-')}.png"
        else:
            filename = "figure.png"
        plt.savefig(filename)


#####
# Basic Rasters / Preprocessing
#####


def raster(raster, cmap, title=None, colorbar=True, ax=None, save=True, gridalpha=0):
    "Plots a raster"

    # Initialize axis
    if ax is None:
        ax = newplot()

    # Reproject to plotting CRS. Replace NoData values with NaN
    raster = raster.copy()
    raster.reproject(crs=CRS)
    values = raster.values.astype(float)
    values[raster.nodata_mask] = nan

    # Plot the raster
    extent = [raster.left, raster.right, raster.bottom, raster.top]
    im = ax.imshow(values, extent=extent, cmap=cmap, interpolation="nearest")

    # Add colorbar and finalize
    if colorbar:
        plt.colorbar(im)
    finalize(ax, title, save, gridalpha)


def mask(mask, title=None, ax=None, save=True, spatial=None, cmap=None, gridalpha=0):
    "Plots a raster mask"

    # Convert mask to Raster object
    if spatial is not None:
        mask = Raster.from_array(mask, nodata=False, spatial=spatial)

    # Plot raster mask in grey
    if cmap is None:
        cmap = mpl.colors.ListedColormap([0.5, 0.5, 0.5])
    raster(mask, cmap, title, colorbar=False, ax=ax, save=save, gridalpha=gridalpha)


def retainments():
    "Adds retainment features to a map"

    # Load the retainment feature dataset
    with fiona.open("retainments.geojson") as collection:
        records = list(collection)
        crs = collection.crs

    # Reproject points to the plotting CRS
    transformer = Transformer.from_crs(crs, CRS, always_xy=True)

    # Plot each retainment feature as a red circle
    for record in records:
        x, y = record.geometry.coordinates
        x, y = transformer.transform(x, y)
        plt.plot(x, y, "ro")


def pr(perimeter, title=None, save=True, spatial=None):
    "Plots the retainment features against the perimeter"
    ax = newplot()
    mask(perimeter, ax=ax, save=False, spatial=spatial)
    retainments()
    finalize(ax, title, save)


#####
# Networks
#####

def segment(feature, color):
    "Plots a LineString feature in the indicated color"
    coords = np.array(feature['geometry']['coordinates'])
    x = coords[:,0]
    y = coords[:,1]
    plt.plot(x, y, color=color)

def segments_fixed_color(segments, color):
    "Plots a stream segment network in a constant color"
    features = segments.geojson(crs=CRS)['features']
    for feature in features:
        segment(feature, color)


def network(
    segments, title=None, perimeter=None, show_retainments=False, save=True, ax=None
):
    "Plots a stream segment network in blue"

    # Create axis. Optionally add perimeter and retainments
    if ax is None:
        ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False, spatial=segments.flow)
    if show_retainments:
        retainments()

    # Plot the segments in blue
    segments_fixed_color(segments, color='blue')
    finalize(ax, title, save)
    return ax


def filter(segments, keep, title=None, perimeter=None, save=True):
    "Plots retained segments in blue, and removable segments in red"

    # First plot the kept segments in blue
    keeping = segments.copy()
    keeping.keep(keep)
    ax = network(keeping, perimeter=perimeter, show_retainments=False, save=False)

    # Then the removed segments in red
    remove = segments.copy()
    remove.remove(keep)
    segments_fixed_color(remove, color='red')
    finalize(ax, title, save)


def outlets(segments, title=None, save=True, show_segments=False, ax=None):
    "Plots the outlets as black circles"

    # Setup the plot
    if ax is None:
        ax = newplot()
    if show_segments:
        network(segments, save=False, ax=ax)

    # Get the geometries
    isterminus = segments.isterminal()
    features = segments.geojson("outlets", crs=CRS)['features']

    # Plot each point as a black dot
    for f, feature in enumerate(features):
        if isterminus[f]:
            x, y = feature['geometry']['coordinates']
            plt.plot(x, y, 'ko')
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

    # Setup the axis
    ax = newplot()
    if perimeter is not None:
        background = mpl.colors.ListedColormap(["white"])
        mask(perimeter, ax=ax, save=False, cmap=background, spatial=segments.flow)
    if show_segments:
        network(segments, save=False, ax=ax)
    if show_outlets:
        outlets(segments, save=False, ax=ax)

    # Get the basin geometries
    features = segments.geojson("basins", crs=CRS)['features']

    # Plot each basin as a pink polygon
    for feature in features:
        shell = feature['geometry']['coordinates'][0]
        shell = np.array(shell)
        polygon = mpl.patches.Polygon(shell, facecolor="pink", edgecolor="black")
        ax.add_patch(polygon)
    finalize(ax, title, save)



#####
# Model Results
#####


def likelihood(segments, probs, title=None, perimeter=None, save=True):
    "Plots the results of the likelihood model on the network"

    # Setup the axis
    ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False, spatial=segments.flow)

    # Get the colormap
    cmap = mpl.colormaps["Reds"]
    colors = cmap(probs)
    norm = mpl.colors.Normalize(vmin=0, vmax=1)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

    # Plot the segments and colorbar
    features = segments.geojson(crs=CRS)['features']
    for feature, color in zip(features, colors):
        segment(feature, color)
    plt.colorbar(mapping, ax=ax)
    finalize(ax, title, save)


def volume(segments, volumes, title=None, perimeter=None, save=True):
    "Plots the volumes on the network"

    # Setup axis
    ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False, spatial=segments.flow)

    # Get colormap
    cmap = mpl.colormaps["Reds"]
    norm = mpl.colors.LogNorm(vmin=1, vmax=1e5)
    cvals = norm(volumes)
    colors = cmap(cvals)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

    # Plot segments and colorbar
    features = segments.geojson(crs=CRS)['features']
    for feature, color in zip(features, colors):
        segment(feature, color)
    plt.colorbar(mapping, ax=ax)
    finalize(ax, title, save)


def hazard(segments, hazard, title=None, perimeter=None, save=True):
    "Plots combined hazard class on the network"

    # Setup axis
    ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False, spatial=segments.flow)

    # Build colormap
    cmap = mpl.colormaps["Reds"]
    norm = mpl.colors.Normalize(vmin=0, vmax=3)
    cvals = norm(hazard)
    colors = cmap(cvals)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

    # Plot segments and colorbar
    features = segments.geojson(crs=CRS)['features']
    for feature, color in zip(features, colors):
        segment(feature, color)
    plt.colorbar(mapping, ax=ax)
    finalize(ax, title, save)


def thresholds(segments, thresholds, title=None, perimeter=None, save=True):
    "Plots rainfall thresholds"

    # Setup axis
    ax = newplot()
    if perimeter is not None:
        mask(perimeter, ax=ax, save=False, spatial=segments.flow)

    # Build colormap
    cmap = mpl.colormaps["Reds_r"]
    norm = mpl.colors.Normalize(vmin=0, vmax=60)
    cvals = norm(thresholds)
    colors = cmap(cvals)
    mapping = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

    # Add segments and colorbar
    features = segments.geojson(crs=CRS)['features']
    for feature, color in zip(features, colors):
        segment(feature, color)
    plt.colorbar(mapping, ax=ax)
    finalize(ax, title, save)