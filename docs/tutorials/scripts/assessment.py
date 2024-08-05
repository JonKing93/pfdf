"Code for the hazard assessment tutorial. Does not include plots"

from pfdf import severity, watershed
from pfdf.models import c10, g14, s17
from pfdf.segments import Segments
from pfdf.utils import intensity

import preprocess

#####
# Input rasters and parameters
#####

# Get preprocessed rasters
perimeter = preprocess.perimeter.values
dem = preprocess.dem
dnbr = preprocess.dnbr
barc4 = preprocess.barc4
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
I15 = [20, 22, 24, 26]
durations_min = [15, 30, 60]
p = [0.5, 0.75]

#####
# Hazard Assessment
#####

# Burn severity masks
isburned = severity.mask(barc4, "burned")
moderate_high = severity.mask(barc4, ["moderate", "high"])

# Watershed analyses
conditioned = watershed.condition(dem)
flow = watershed.flow(conditioned)
slopes = watershed.slopes(dem, flow)
relief = watershed.relief(dem, flow)

# Flow accumulations
pixel_area_km2 = dem.pixel_area(units="kilometers")
area_km2 = watershed.accumulation(flow, times=pixel_area_km2).values
burned_area_km2 = watershed.accumulation(flow, mask=isburned, times=pixel_area_km2).values
nretainments = watershed.accumulation(flow, mask=retainments).values

# Build the mask to delineate an initial network
large_enough = area_km2 >= min_area_km2
below_burn = burned_area_km2 >= min_burned_area_km2
below_retainment = nretainments > 0
at_risk = perimeter | below_burn
mask = large_enough & at_risk & ~iswater & ~below_retainment

# Delineate a stream segment network
segments = Segments(flow, mask, max_length_m)

# Compute physical variables for the stream segments
area_km2 = segments.area()
burn_ratio = segments.burn_ratio(isburned)
slope = segments.slope(slopes)
confinement = segments.confinement(dem, neighborhood)
developed_area_km2 = segments.developed_area(isdeveloped)
in_perimeter = segments.in_perimeter(perimeter)

# Locate stream segments that meet physical criteria for debris-flow risk
floodlike = area_km2 > max_area_km2
burned = burn_ratio >= min_burn_ratio
steep = slope >= min_slope
confined = confinement <= max_confinement
undeveloped = developed_area_km2 <= max_developed_area_km2

# Filter the network, but prioritize flow continuity
at_risk = burned & steep & confined & undeveloped
keep = ~floodlike & (in_perimeter | at_risk)
keep = segments.continuous(keep)
segments.keep(keep)

# Likelihood (M1 model)
R15 = intensity.to_accumulation(I15, durations=15)
B, Ct, Cf, Cs = s17.M1.parameters(durations=15)
T, F, S = s17.M1.variables(segments, moderate_high, slopes, dnbr, kf, omitnan=True)
likelihoods = s17.likelihood(R15, B, Ct, T, Cf, F, Cs, S)

# Volume model
Bmh_km2 = segments.burned_area(moderate_high)
relief = segments.relief(relief)
volumes, Vmin, Vmax = g14.emergency(I15, Bmh_km2, relief)

# Combined hazard classification
p_thresholds = [0.2, 0.4, 0.6, 0.8]
hazard = c10.hazard(likelihoods[:, 2], volumes[:, 2], p_thresholds=p_thresholds)

# Rainfall thresholds (M1 model)
B, Ct, Cf, Cs = s17.M1.parameters(durations=durations_min)
accumulations = s17.accumulation(p, B, Ct, T, Cf, F, Cs, S)
intensities = intensity.from_accumulation(accumulations, durations_min)
