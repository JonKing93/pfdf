"""
Modules that implement hazard assessment models
----------
Modules:
    staley2017  - Debris flow likelihood and rainfall accumulation thresholds
    gartner2014 - Potential sediment volumes
    cannon2010  - Combined hazard classification scheme

Aliases:
    s17         - Alias of the staley2017 module
    g14         - Alias of the gartner2014 module
    c10         - Alias of the cannon2010 module
"""

import pfdf.models.cannon2010 as c10
import pfdf.models.gartner2014 as g14
import pfdf.models.staley2017 as s17
