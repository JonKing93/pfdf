"Code for the 'export' portion of the assessment tutorial."

import assessment

# Load values from the assessment
area_km2 = assessment.area_km2
Bmh_km2 = assessment.Bmh_km2
burn_ratio = assessment.burn_ratio
confinement = assessment.confinement
developed_area_km2 = assessment.developed_area_km2
F = assessment.F
hazard = assessment.hazard
intensities = assessment.intensities
kept = assessment.keep
likelihood = assessment.likelihoods
relief = assessment.relief
S = assessment.S
segments = assessment.segments
T = assessment.T
slope = assessment.slope
volume = assessment.volumes
Vmin = assessment.Vmin
Vmax = assessment.Vmax

# Limit earth system variables to the segments kept in the network
area_km2 = area_km2[kept]
burn_ratio = burn_ratio[kept]
slope = slope[kept]
confinement = confinement[kept]
developed_area_km2 = developed_area_km2[kept]

# Collect data properties for export
properties = {
    # Hazard assessment results
    "hazard": hazard,
    "p_15min_24mm": likelihood[:, 2],
    "V_24mm": volume[:, 2],
    "Vmin_24mm": Vmin[:, 2],
    "Vmax_24mm": Vmax[:, 2],
    "I_15min_50": intensities[:, 0, 0],

    # Variables used to run models
    "T": T,
    "F": F,
    "S": S,
    "relief": relief,
    "Bmh_km2": Bmh_km2,
    
    # Earth system variables
    "area_km2": area_km2,
    "burn_ratio": burn_ratio,
    "slope": slope,
    "confinement": confinement,
    "dev_area_km2": developed_area_km2,
}

# Save segments as LineString features
segments.save("segments.geojson", properties, overwrite=True)

# Remove nested basins
nested = segments.isnested()
segments.remove(nested)

# Collect data properties for terminal basins/outlets
properties = {
    "hazard": hazard[~nested],
    "p_24mm": likelihood[~nested, 2],
    "V_24mm": volume[~nested, 2],
    "I_15min_50": intensities[~nested, 0, 0],
    "area_km2": area_km2[~nested],
}

# Save basins as polygons and outlets as points
segments.save("outlets.geojson", "outlets", properties, overwrite=True)
segments.save("basins.geojson", "basins", properties, overwrite=True)
