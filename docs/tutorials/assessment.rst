Assessment Tutorial
===================

This tutorial examines the steps needed to implement a basic hazard assessment. Specifically, this assessment is for the `2016 San Gabriel Complex fire <https://en.wikipedia.org/wiki/San_Gabriel_Complex_Fire>`_, which burned a portion of the Angeles National Forest. In the tutorial, we will:

* Perform a watershed analysis
* Delineate a stream segment network
* Filter the network to model-worthy segments
* Run hazard models, and
* Save the results to file

The assessment relies on rasters from the :doc:`preprocessing tutorial <preprocess>`, which we recommend reading first.

.. admonition:: Download

  You can download the datasets and scripts used in this tutorial here: :doc:`Download Files <download>`. This tutorial follows the ``assessment`` and ``export`` scripts. See also ``assessment_plots`` to reproduce the figures.


Input Datasets
--------------
We will use various preprocessed rasters to implement the hazard assessment. As a reminder, these are:

.. list-table::

    * - **Raster**
      - **Description**
    * - perimeter
      - Mask of the burned area. Defines the domain of the assessment.
    * - dem
      - Digital elevation model. Used to compute flow directions.
    * - dnbr
      - Provides a measure of burn severity and is used by hazard assessment models.
    * - severity
      - Divides burn severity into 4 classes. Used to delineate a network and run models.
    * - kf-factor
      - Soil KF-factors. Used to implement the :doc:`models of Staley et al., 2017 </guide/models/s17>`.
    * - retainments
      - A mask of features designed to stop debris flows. Used to design the initial network.
    * - iswater
      - A mask of water bodies. Used to design the initial network.
    * - isdeveloped
      - A mask of human-developed terrain. Used to design the initial network.


First Steps
-----------

Getting Started
+++++++++++++++

We'll start by importing the :doc:`severity module </guide/misc/severity>`, :doc:`watershed module </guide/watershed>`, :doc:`Segments class </guide/segments/index>`, and the :doc:`hazard assessment models </guide/models/index>`:

.. include:: download/code/assessment.py
    :code:
    :start-line: 2
    :end-line: 5

We'll also import the script from the :doc:`preprocessing tutorial <preprocess>`, which we'll use to load the various preprocessed rasters:

.. include:: download/code/assessment.py
    :code:
    :start-line: 6
    :end-line: 7

.. include:: download/code/assessment.py
    :code:
    :start-line: 13
    :end-line: 21

Note that we loaded the data array (``.values``) directly for the perimeter, water, and development masks. This is because these rasters are boolean arrays that we'll use for logical operations.

.. tab-set::

    .. tab-item:: DEM

        .. image:: /images/assessment/dem.png

    .. tab-item:: Perimeter

        .. image:: /images/assessment/fire-perimeter.png

    .. tab-item:: dNBR

        .. image:: /images/assessment/dnbr.png

    .. tab-item:: Burn Severity

        .. image:: /images/assessment/burn-severity.png

    .. tab-item:: KF-factor

        .. image:: /images/assessment/kf-factor.png

    .. tab-item:: Retainments

        .. image:: /images/assessment/retainment-features.png

    .. tab-item:: Water Mask

        .. image:: /images/assessment/water-mask.png

    .. tab-item:: Development Mask

        .. image:: /images/assessment/development-mask.png


Burn Severity Masks
+++++++++++++++++++

Next, we'll use the :ref:`severity.mask function <pfdf.severity.mask>` to create two masks from the burn severity raster. We'll use these masks at various points throughout the assessment:

.. include:: download/code/assessment.py
    :code:
    :start-line: 51
    :end-line: 53

.. tab-set::

    .. tab-item:: Burn Mask

        .. image:: /images/assessment/burn-mask.png

    .. tab-item:: Moderate-High Mask

        .. image:: /images/assessment/mod-high.png


Watershed Analysis
++++++++++++++++++

Next, we'll use the :doc:`watershed module </guide/watershed>` to analyze the watershed. We'll start by using a conditioned DEM to compute flow directions:

.. include:: download/code/assessment.py
    :code:
    :start-line: 55
    :end-line: 57

.. image:: /images/assessment/flow-directions.png


We'll use the flow directions to compute flow slopes and vertical relief, which we'll use later in the assessment:

.. include:: download/code/assessment.py
    :code:
    :start-line: 57
    :end-line: 59

Finally, we'll compute several types of flow accumulation. 

.. include:: download/code/assessment.py
    :code:
    :start-line: 60
    :end-line: 63

.. list-table::
    :header-rows: 1
    
    * - Accumulation
      - Description
    * - ``npixels``
      - The number of catchment pixels for each point.
    * - ``nburned``
      - The number of burned pixels in each the catchment.
    * - ``nretainments``
      - The number of debris-flow retainment features above each point.

We'll use these accumulation rasters to create a network delineation mask in the next section.


Stream Network
--------------

Delineation Mask
++++++++++++++++
To create a stream segment network, we'll first need a network delineation mask. This mask is used to exclude non-viable pixels from the stream segment network. False pixels will never be included in a stream segment. By contrast, a True pixel *may* be included in a stream segment, but there's no guarantee.

As a starting point, most masks should exclude pixels with catchments that are too small to generate a debris flow. We'll also exclude catchments that are negligibly burned, as these areas are unlikely to exhibit altered debris-flow hazards. Finally, we'll exclude pixels below debris-flow retainment features, as debris flows are unlikely to proceed beyond these points.

We'll start by defining two parameters:

.. include:: download/code/assessment.py
    :code:
    :start-line: 23
    :end-line: 25

Here, ``min_area_km2`` defines the minimum catchment area (in km^2). Smaller catchments are usually too small to be able to generate a debris-flow. The ``min_burned_area_km2`` parameter defines the minimum burned catchment area (also km^2). Catchments with smaller burned areas are negligibly affected by the fire. We can combine these thresholds with the various flow accumulation rasters to generate the network delineation mask.

We've expressed these parameters in terms of areas, but the :ref:`accumulation <pfdf.watershed.accumulation>` function accumulates pixels, rather than areas. To accommodate this, we'll next convert our areas to pixel counts:

.. include:: download/code/assessment.py
    :code:
    :start-line: 46
    :end-line: 49

We can now use these pixel counts to start building raster masks:

.. include:: download/code/assessment.py
    :code:
    :start-line: 65
    :end-line: 69

The ``large_enough`` mask indicates catchments that are large enough to generate debris flow, and the ``below_retainment`` mask indicates areas that are below a retainment feature. The ``below_burn`` mask indicates areas that may have altered debris-flow hazards. We'll combine the ``below_burn`` mask with the fire perimeter mask to generate an ``at_risk`` mask. This is not stricly necessary, as there may be areas within the perimeter that aren't below any burned area. However, removing segments within the perimeter can sometimes cause confusion from a communication standpoint, as stakeholders may interpret the missing segments as an incomplete assessment. We use the perimeter because this tutorial is focused on hazard assessments, but note that this may not be necessary for all cases:

.. tab-set::

    .. tab-item:: At Risk

        .. image:: /images/assessment/at-risk.png

    .. tab-item:: Large Enough

        .. image:: /images/assessment/large-enough.png

    .. tab-item:: Below Burn

        .. image:: /images/assessment/below-burn.png

    .. tab-item:: Below Retainment

        .. image:: /images/assessment/below-retainment.png


We'll now combine these masks to create the final network-delineation mask. We will exclude small catchments, areas with negligible burn, water bodies, and pixels below retainment features:

.. include:: download/code/assessment.py
    :code:
    :start-line: 69
    :end-line: 70

.. image:: /images/assessment/mask.png

.. note::

    Depending on the size of your screen, the mask may look like a series of disjointed pixels. In reality, most of the pixels connect continuously.


Delineate Network
+++++++++++++++++
We're almost ready to delineate a stream network. Let's define one additional parameter first:

.. include:: download/code/assessment.py
    :code:
    :start-line: 25
    :end-line: 26

This parameter establishes a maximum length for segments in the network. Segments longer than this length will be split into multiple pieces. We can now use the :ref:`Segments constructor <pfdf.segments.Segments.__init__>` to create an initial network:

.. include:: download/code/assessment.py
    :code:
    :start-line: 72
    :end-line: 73

.. figure:: /images/assessment/initial-network.png

    An initial stream segment network. Blue lines indicate the stream segments. The grey background is the fire perimeter, and the red dots are debris-retention features.

We can use the ``length`` parameter to see that there are 658 segments in this network::

    >>> segments.length
    658


.. _filter-tutorial:
    
Filter Network
++++++++++++++
Our next step is to filter the network. Here, we will remove segments that don't meet physical criteria common to debris flows. Specifically, we'll consider:

Catchment Area
    Segments with very large catchments will exhibit flood-like behavior, rather than debris-flow behavior. As such, we'll remove segments whose catchments are too large.

Burn Ratio
    The catchment must be sufficiently burned, or it will be negligibly affected by the fire. Here, we'll remove segments whose catchments are insufficiently burned.

Slope
    Debris flows are most common in areas with steep slopes, as shallow slopes can lead to sediment deposition, rather than debris flow. We'll remove segments whose slopes are too shallow.

Confinement Angle
    Debris flows are more common in confined areas, as open areas can allow debris deposition, rather than flow. We'll remove segments that are insufficiently confined.

Developed Area
    Human development can alter the course and behavior of debris flows, so we'll remove segments that contain large amounts of human development.

In Perimeter
    As discussed previously, we'll retain most segments within the fire perimeter, as stakeholders may interpret missing segments as an incomplete assessment.

We'll start by defining several filtering parameters:

.. include:: download/code/assessment.py
    :code:
    :start-line: 28
    :end-line: 34

Most of the parameters define a threshold for one of the filtering variables. The final ``neighborhood`` parameter indicates the number of pixels in the radius of the focal window used to compute confinement angles. Next, we'll use the ``segments`` object to compute the filtering variables for each segment

.. include:: download/code/assessment.py
    :code:
    :start-line: 75
    :end-line: 81

Here, the output variables are 1D numpy arrays with one element per segment in the network. We'll then compare the variables to the thresholds. The resulting arrays are boolean vectors with one element per segment:

.. include:: download/code/assessment.py
    :code:
    :start-line: 83
    :end-line: 89

Visualizing these arrays, we use blue lines to indicate segments that meet a physical criterion, and red lines to indicate segments that fail a criterion for debris flow risk:

.. tab-set::

    .. tab-item:: Not Flood-like

        .. image:: /images/assessment/floodlike.png

    .. tab-item:: Burned

        .. image:: /images/assessment/burned.png

    .. tab-item:: Steep

        .. image:: /images/assessment/steep.png

    .. tab-item:: Confined

        .. image:: /images/assessment/confined.png

    .. tab-item:: Undeveloped

        .. image:: /images/assessment/undeveloped.png

    .. tab-item:: In Perimeter

        .. image:: /images/assessment/in-perimeter.png


Finally, we'll use these arrays to filter the network. We'll remove all flood-like segments, and we'll retain segments that either (1) are in the fire perimeter, or (2) meet the physical criteria for debris-flow hazards:

.. include:: download/code/assessment.py
    :code:
    :start-line: 91
    :end-line: 94

.. tab-set::

    .. tab-item:: Filtered Network

        .. image:: /images/assessment/filtered-network.png

    .. tab-item:: Indicated Segments

        .. image:: /images/assessment/keep-segments.png

If we compare the filtered network to the indicated segments, we can see that the :ref:`keep command <pfdf.segments.Segments.keep>` retained 4 extra segments in the network::
    
    >>> np.sum(keep)
    466
    >>> print(segments.length)
    470
    
This is because we used :ref:`keep <pfdf.segments.Segments.keep>` in its default configuration, which prioritizes :ref:`flow continuity <flow-continuity>` over removing segments. Thus, the command may retain additional segments in the network. As such, we return the ``kept`` output. This is a 1D boolean numpy array with one element per segment in the *initial* network. The True elements of the array indicate the segments that were actually retained. We'll use this array later to help save the segments to file.


Hazard Models
-------------

We've finished designing the stream network, so we're now ready to implement the hazard models. Specifically, we'll run 

* The M1 probability/rainfall accumulation model of :doc:`Staley et al., 2017 </guide/models/s17>`
* The emergency sediment volume model of :doc:`Gartner et al., 2014 </guide/models/g14>`, and
* The combined hazard classification scheme of :doc:`Cannon et al., 2010 </guide/models/c10>`


Probability / Accumulation
++++++++++++++++++++++++++

We'll start with the probability / accumulation model. This is implemented by the :doc:`s17 module </guide/models/s17>`. We'll start by defining several parameters used to implement the models:

.. include:: download/code/assessment.py
    :code:
    :start-line: 36
    :end-line: 39

Here, ``p`` is a set of debris-flow probability levels; we'll use the model to determine the rainfall accumulations needed to achieve these probabilities. Conversely, ``R_mm`` is a set of rainfall accumulations, and we'll also use the model to calculate the probability levels associated with these accumulations. Finally, ``durations_min`` is a set of rainfall durations used to calibrate the M1 model; we'll solve the probability and accumulation for each of these durations.

Our next step is to compute the parameters and variables for the M1 model:

.. include:: download/code/assessment.py
    :code:
    :start-line: 96
    :end-line: 98

Here, each of the parameters (``B``, ``Ct``, ``Cf``, and ``Cs``) is a vector with 3 elements - each element is the parameter value for one of our queried rainfall durations. By contrast, each variable (``T``, ``F``, and ``S``) is a vector with one element per stream segment.

We'll then use these quantities to solve for debris-flow probability, given a set of rainfall accumulations, and vice versa:

.. include:: download/code/assessment.py
    :code:
    :start-line: 98
    :end-line: 100

Here, the ``probability`` and ``accumulation`` outputs are 3D numpy arrays. The number of rows corresponds to the number of segments in the network. Each column holds the solutions for one of our queried rainfall durations. Each element along the third dimension holds the solutions for one of the given probability levels / rainfall accumulations::

    >>> probability.shape
    (470, 3, 4)
    >>> probability.shape == (segments.length, len(durations_min), len(R_mm))
    True

    >>> accumulation.shape
    (470, 3, 2)
    >>> accumulation.shape == (segments.length, len(durations_min), len(p))
    True

Let's visualize the results for the probability model, using 6 mm of rainfall over a 15-minute interval (``probability[:, 0, 1]``). This is equivalent to a peak 15-minute *intensity* of 24 mm/hour. Here, we can see that this amount of rainfall would cause a high probability of debris-flow probability for many of the segments:

.. figure:: /images/assessment/probability.png

    Modeled debris-flow probabilities given 6 mm of rainfall over a 15-minute duration (equivalent to 24mm/hour). Darker shades of red correspond to increased debris-flow probability.

Volume Model
++++++++++++
Next, we'll model the potential sediment volume of any debris flows using the :doc:`g14 module </guide/models/g14>`. We'll start by defining a parameter:

.. include:: download/code/assessment.py
    :code:
    :start-line: 39
    :end-line: 40

This is the peak 15-minute rainfall intensity (in mm/hour) for which we'd like to solve the model. Next, we'll compute two variables for the segments:

.. include:: download/code/assessment.py
    :code:
    :start-line: 102
    :end-line: 104

These are (1) the catchment area burned at moderate-or-high severity, and (2) the vertical relief for each segment. The output ``Bmh_km2`` and ``relief`` variables are both numpy 1D arrays with one element per segment. Finally, we'll solve the emergency-assessment sediment volume model for these quantities:

.. include:: download/code/assessment.py
    :code:
    :start-line: 104
    :end-line: 105

The ``volume`` output is a 2D numpy array with one row per stream segment, and one column per queried rainfall intensity::

    >>> volume.shape
    (470, 4)
    >>> volume.shape == (segments.length, len(i15))
    True

Let's visualize the results for a 24 mm/hour rainfall intensity (``volume[:,2]``):

.. figure:: /images/assessment/volume.png

    Modeled potential sediment volumes given a peak 15-minute rainfall intensity of 24 mm / hour (equivalent to 6 mm in 15 minutes). Darker shades of red indicate larger potential sediment volumes.



Combined Hazard
+++++++++++++++
Finally, we'll use the :doc:`c10 module </guide/models/c10>` to classify the relative hazard, based on the modeled debris-flow probabilities and volumes. The original model defines 4 probability classes, but we'll use the ``p_thresholds`` variable to define 5 such classes instead:

.. include:: download/code/assessment.py
    :code:
    :start-line: 107
    :end-line: 108

Then, we'll classify the relative hazard resulting from a peak 15-minute rainfall intensity of 24 mm/hour. This corresponds to a rainfall accumulation of 6 mm/15-minutes (``probability[:,0,1]`` and ``volume[:,2]``):

.. include:: download/code/assessment.py
    :code:
    :start-line: 108
    :end-line: 109

.. figure:: /images/assessment/hazard.png

    The combined hazard classification for a peak 15-minute rainfall intensity of 24 mm/hour. Darker shades indicate greater hazard.


Export
------

.. note::

    This section follows the ``export`` script in the downloaded resources.

We've illustrated much of this tutorial using `matplotlib <https://matplotlib.org/>`_, but it's often useful to export assessment results to a standard GIS format instead. For example, as a ShapeFile or GeoJSON. In this final section, we'll examine how to export results as:

* A set of stream segments (LineString geometry),
* Outlets (Point geometry), and
* Outlet Basins (Polygon geometry)

We'll do this using the :ref:`save method <pfdf.segments.Segments.save>`, and we'll include various results from our assessment, including hazard model results, model inputs, and earth-system variables for the segments. These variables are entirely arbitrary - you are not required to include them in your own assessments, and you may include any other quantities as well.

.. tip:: 
    
    This tutorial saves outputs as GeoJSON files, but you can use :ref:`most other GIS formats <vector-drivers>` instead. For example, change the ``.geosjon`` file extensions to ``.shp`` to save the outputs as ShapeFiles.


Segments
++++++++
We'll start by exporting the stream segments. ALthough we could use the :ref:`save method <pfdf.segments.Segments.save>` in its basic configuration to save the segment locations, we'd like to also include assessment results. As such, we'll need to build a properties ``dict``, which will hold the values we want to save to file.

As stated, we'd like to save assessment results, hazard model inputs, and the earth-system variables we calculated for the stream segments. The earth-system variables present a challenge, because we calculated them for every variable in the initial (unfiltered) network. By contrast, we only want to export the final (filtered) network to file. Looking back to the :ref:`filtering section <filter-tutorial>`, recall the ``kept`` variable we returned as output from the :ref:`keep method <pfdf.segments.Segments.keep>`. This boolean array indicates the segments in the initial network that remained in the final network. We can use this array to select values for the segments in the final network:

.. include:: download/code/export.py
    :code:
    :start-line: 23
    :end-line: 28

Now that we've updated these variables, we can build the properties ``dict``:

.. include:: download/code/export.py
    :code:
    :start-line: 30
    :end-line: 51

The keys of the dict should be strings, which represent the variable names. The values should be numeric vectors with one element per stream segment.

.. note::

    These names and variables are arbitrary. We could have used different names or different variables if needed.

We can now save the segments to file:

.. include:: download/code/export.py
    :code:
    :start-line: 53
    :end-line: 54

The segments will have LineString geometries, and will resemble the following:

.. figure:: /images/assessment/segments.png

    The segment LineString geometries in blue.


Outlets
+++++++
We'll also export the network's :ref:`outlets <export-types>`. These are Point geometries that indicate where segments flow out of the network. We'll need to build a separate property dict for the outlets, because the number of outlets will be less than the number of segments. The ``isterminus`` property is useful for this; it returns a boolean array indicating which segments are terminal segments (i.e. segments that flow out of the network). We'll use this to create a new property dict:

.. include:: download/code/export.py
    :code:
    :start-line: 56
    :end-line: 64

.. note::

    For the sake of brevity, we've only included hazard model results in this property dict.

We can now export the outlets by calling :ref:`save <pfdf.segments.Segments.save>` and setting ``type="outlets"``:

.. include:: download/code/export.py
    :code:
    :start-line: 66
    :end-line: 67

These features will resemble the following:

.. figure:: /images/assessment/outlets.png

    The outlet points for the network as black circles.

If we combine the outlets with the segments, we can see that the outlets occur wherever a segment flows out of the network:

.. figure:: /images/assessment/outlets-and-segments.png

    The outlet points (black circles), and segment LineStrings (blue lines).


Basins
++++++
We'll also export the :ref:`outlet basins <export-types>`. These are Polygon geometries, and each represents the catchment draining into an outlet point. The number of terminal basins will match the number of terminal outlets, so we can re-use the property dict from the previous section. Then, we can export the basins by calling the :ref:`save method <pfdf.segments.Segments.save>` and setting ``type="basins"``:

.. include:: download/code/export.py
    :code:
    :start-line: 67
    :end-line: 68
    
The basins will resemble the following:

.. figure:: /images/assessment/basins.png

    The terminal basins as pink polygons.

If we combine the basins with the segments and outlet points, we can see that each basin contains all the segments that drain to a particular outlet point:

.. figure:: /images/assessment/basins-segments.png

    Terminal basins (pink polygons), stream segments (blue lines), and outlet points (black points).


Putting it all together
-----------------------

**Hazard Assessment**

.. include:: download/code/assessment.py
    :code:
    :start-line: 2
    :end-line: 109

**Export**

.. include:: download/code/export.py
    :code:
    :start-line: 22
    :end-line: 68

