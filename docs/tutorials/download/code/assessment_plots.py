"Code for the hazard assessment tutorial. Does not include plots"

from pfdf.segments import Segments
from pfdf import severity, watershed
from pfdf.models import s17, g14, c10

import preprocess
import plot


#####
# Input rasters and parameters
#####

# Get preprocessed rasters
perimeter = preprocess.perimeter
dem = preprocess.dem
dnbr = preprocess.dnbr
barc4 = preprocess.severity
kf = preprocess.kf
retainments = preprocess.retainments
iswater = preprocess.iswater.values
isdeveloped = preprocess.isdeveloped.values

plot.mask(perimeter, "Fire Perimeter")
plot.raster(dem, title="DEM", cmap="terrain")
plot.raster(dnbr, title="dNBR", cmap="OrRd")
plot.raster(barc4, title="Burn Severity", cmap="OrRd")
plot.raster(kf, title="KF-factor", cmap="Oranges")
plot.pr(perimeter, "Retainment Features")
plot.mask(iswater, title="Water Mask", spatial=dem)
plot.mask(isdeveloped, title="Development Mask", spatial=dem)

# Parameters for building the network
min_area_km2 = 0.025
min_burned_area_km2 = 0.01
max_length_m = 500

# Parameters for filtering the network
min_burn_ratio = 0.25
min_slope = 0.12
max_confinement = 174
neighborhood = 4
max_area_km2 = 8
max_developed_area_km2 = 0.025

# Parameters for hazard modeling
p = [0.5, 0.75]
R_mm = [3, 6, 9, 12]
durations_min = [15, 30, 60]
i15 = [20, 22, 24, 26]

#####
# Hazard Assessment
#####

# Convert areas to pixel counts
pixel_area_km2 = dem.pixel_area / 1e6
min_pixels = min_area_km2 / pixel_area_km2
min_burned_pixels = min_burned_area_km2 / pixel_area_km2

# Burn severity masks
isburned = severity.mask(barc4, "burned")
moderate_high = severity.mask(barc4, ["moderate", "high"])

plot.mask(isburned, "Burn Mask", save="burn-mask.png")
plot.mask(moderate_high, "Moderate or High Severity", save="mod-high.png")

# Watershed analysis
conditioned = watershed.condition(dem)
flow = watershed.flow(conditioned)
slopes = watershed.slopes(dem, flow)
relief = watershed.relief(dem, flow)

npixels = watershed.accumulation(flow).values
nburned = watershed.accumulation(flow, mask=isburned).values
nretainments = watershed.accumulation(flow, mask=retainments).values

plot.raster(flow, cmap="viridis", title="Flow Directions")

# Build the mask to delineate an initial network
in_perimeter = perimeter.values
large_enough = npixels >= min_pixels
below_retainment = nretainments > 0
below_burn = nburned >= min_burned_pixels
at_risk = in_perimeter | below_burn
mask = large_enough & at_risk & ~iswater & ~below_retainment

plot.mask(large_enough, "Large Enough", spatial=dem)
plot.mask(below_burn, "Below Burn", spatial=dem)
plot.mask(below_retainment, "Below Retainment", spatial=dem)
plot.mask(at_risk, "At Risk", spatial=dem)
plot.mask(mask, "Network Delineation Mask", spatial=dem, save="mask.png")

# Delineate a stream segment network
segments = Segments(flow, mask, max_length_m)
plot.network(segments, "Initial Network", perimeter, show_retainments=True)

# Compute physical variables for the stream segments
area_km2 = segments.area() / 1e6
burn_ratio = segments.burn_ratio(isburned)
slope = segments.slope(slopes)
confinement = segments.confinement(dem, neighborhood)
developed_area_km2 = segments.developed_area(isdeveloped) / 1e6
in_perimeter = segments.summary("max", in_perimeter)

# Locate stream segments that meet physical criteria for debris-flow risk
floodlike = area_km2 > max_area_km2
burned = burn_ratio >= min_burn_ratio
steep = slope >= min_slope
confined = confinement <= max_confinement
undeveloped = developed_area_km2 <= max_developed_area_km2
in_perimeter = in_perimeter > 0

plot.filter(segments, ~floodlike, "Not Flood-like", perimeter, save="floodlike.png")
plot.filter(segments, burned, "Burned", perimeter)
plot.filter(segments, steep, "Steep Slope", perimeter, save="steep.png")
plot.filter(segments, confined, "Confined", perimeter)
plot.filter(segments, undeveloped, "Undeveloped", perimeter)
plot.filter(segments, in_perimeter, "In Perimeter", perimeter)

# Filter the network, but prioritize flow continuity
at_risk = burned & steep & confined & undeveloped
keep = ~floodlike & (in_perimeter | at_risk)
plot.filter(segments, keep, "Keep Segments", perimeter)

kept = segments.keep(indices=keep)
plot.network(segments, "Filtered Network", perimeter)

# Probability and accumulation (M1 model)
B, Ct, Cf, Cs = s17.M1.parameters(durations=durations_min)
T, F, S = s17.M1.variables(segments, moderate_high, slopes, dnbr, kf, omitnan=True)
probability = s17.probability(R_mm, B, Ct, T, Cf, F, Cs, S)
accumulation = s17.accumulation(p, B, Ct, T, Cf, F, Cs, S)

plot.probability(
    segments, probability[:, 0, 1], "Probability", perimeter, save="probability.png"
)

# Volume model
Bmh_km2 = segments.burned_area(moderate_high) / 1e6
relief = segments.relief(relief)
volume = g14.emergency(i15, Bmh_km2, relief)

plot.volume(segments, volume[:, 2], "Volume", perimeter)

# Combined hazard classification
p_thresholds = [0.2, 0.4, 0.6, 0.8]
hazard = c10.hazard(probability[:, 0, 1], volume[:, 2], p_thresholds=p_thresholds)
plot.hazard(segments, hazard, "Combined Hazard", perimeter, save="hazard.png")

# Plot exported features
plot.network(segments, "Segments")
plot.outlets(segments, "Outlets")
plot.outlets(segments, "Outlets and Segments", show_segments=True)

segments.locate_basins()
plot.basins(segments, "Basins", perimeter)
plot.basins(
    segments,
    "Basins, Segments, Outlets",
    perimeter,
    show_outlets=True,
    show_segments=True,
    save="basins-segments.png",
)
