"Code for the hazard assessment tutorial. Does not include plots"

from pfdf import severity, watershed
from pfdf.models import c10, g14, s17
from pfdf.segments import Segments

import preprocess

#####
# Input rasters and parameters
#####

# Get preprocessed rasters
in_perimeter = preprocess.perimeter.values
dem = preprocess.dem
dnbr = preprocess.dnbr
barc4 = preprocess.severity
kf = preprocess.kf
retainments = preprocess.retainments
iswater = preprocess.iswater.values
isdeveloped = preprocess.isdeveloped.values

# Parameters for building the network
min_area_km2 = 0.025
min_burned_area_km2 = 0.01
max_length_m = 500

# Parameters for filtering the network
min_burn_ratio = 0.25
min_slope = 0.12
max_area_km2 = 8
max_developed_area_km2 = 0.025
max_confinement = 174
neighborhood = 4

# Parameters for hazard modeling
p = [0.5, 0.75]
R_mm = [16, 24, 32, 34]
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

# Watershed analysis
conditioned = watershed.condition(dem)
flow = watershed.flow(conditioned)
slopes = watershed.slopes(dem, flow)
relief = watershed.relief(dem, flow)

npixels = watershed.accumulation(flow).values
nburned = watershed.accumulation(flow, mask=isburned).values
nretainments = watershed.accumulation(flow, mask=retainments).values

# Build the mask to delineate an initial network
large_enough = npixels >= min_pixels
below_burn = nburned >= min_burned_pixels
below_retainment = nretainments > 0
at_risk = in_perimeter | below_burn
mask = large_enough & at_risk & ~iswater & ~below_retainment

# Delineate a stream segment network
segments = Segments(flow, mask, max_length_m)

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

# Filter the network, but prioritize flow continuity
at_risk = burned & steep & confined & undeveloped
keep = ~floodlike & (in_perimeter | at_risk)
kept = segments.keep(indices=keep)

# Probability and accumulation (M1 model)
B, Ct, Cf, Cs = s17.M1.parameters(durations=durations_min)
T, F, S = s17.M1.variables(segments, moderate_high, slopes, dnbr, kf, omitnan=True)
probability = s17.probability(R_mm, B, Ct, T, Cf, F, Cs, S)
accumulation = s17.accumulation(p, B, Ct, T, Cf, F, Cs, S)

# Volume model
Bmh_km2 = segments.burned_area(moderate_high) / 1e6
relief = segments.relief(relief)
volume = g14.emergency(i15, Bmh_km2, relief)

# Combined hazard classification
p_thresholds = [0.2, 0.4, 0.6, 0.8]
hazard = c10.hazard(probability[:, 0, 1], volume[:, 2], p_thresholds=p_thresholds)
