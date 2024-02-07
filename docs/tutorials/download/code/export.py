"Code for the 'export' portion of the assessment tutorial."

import assessment

# Load values from the assessment
accumulation = assessment.accumulation
area_km2 = assessment.area_km2
Bmh_km2 = assessment.Bmh_km2
burn_ratio = assessment.burn_ratio
confinement = assessment.confinement
developed_area_km2 = assessment.developed_area_km2
F = assessment.F
hazard = assessment.hazard
kept = assessment.kept
probability = assessment.probability
relief = assessment.relief
S = assessment.S
segments = assessment.segments
T = assessment.T
slope = assessment.slope
volume = assessment.volume

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
    "p_15min_24mm": probability[:, 0, 1],
    "R_15min_50": accumulation[:, 0, 0],
    "V_24mm": volume[:, 2],
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

# Collect data properties for terminal basins/outlets
terminal = segments.isterminus
properties = {
    "hazard": hazard[terminal],
    "p_15min_24mm": probability[terminal, 0, 1],
    "R_15min_50": accumulation[terminal, 0, 0],
    "V_24mm": volume[terminal, 2],
    "area_km2": area_km2[terminal],
}

# Save basins as polygons and outlets as points
segments.save("outlets.geojson", properties, type="outlets", overwrite=True)
segments.save("basins.geojson", properties, type="basins", overwrite=True)
