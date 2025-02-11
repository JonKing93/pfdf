FAQs / Troubleshooting
======================

Answers to frequently asked questions and tips for troubleshooting.

* :ref:`faq-stripes`
* :ref:`faq-condition`
* :ref:`faq-flowdir`
* :ref:`faq-geodatabase`
* :ref:`faq-error-os`
* :ref:`faq-error-pysheds`


----

.. _faq-stripes:

Assessment has lots of parallel / striped stream segments and basins
--------------------------------------------------------------------
This usually indicates a failure of the DEM conditioning algorithm. This algorithm is known to struggle in flat terrain, so excluding flat areas from your analysis can help. Alternatively, try conditioning the DEM with a third-party tool before using it as input.


.. _faq-condition:

Can I use a different tool to condition the DEM?
------------------------------------------------
Yes, this is fine, and may help improve areas where the pfdf conditioning algorithm struggles (such as in flat terrain).


.. _faq-flowdir:

Can I use a different tool to compute flow directions?
------------------------------------------------------
Yes, but the computed flow directions should adhere to the :ref:`TauDEM style <taudem-style>`.


.. _faq-geodatabase:

How do I rasterize features in a geodatabase?
---------------------------------------------
You can use the :ref:`Raster.from_points <pfdf.raster.Raster.from_points>` and/or :ref:`Raster.from_polygons <pfdf.raster.Raster.from_polygons>` commands as usual. If the geodatabase includes multiple feature layers, then you should set the ``layer`` option to the name of the targeted data layer. For example::

    Raster.from_polygons('my-geodatabase.gdb', layer='My_Data_Layer')


.. _faq-error-os:

I'm getting arcane errors referencing the operating system
----------------------------------------------------------
This may indicate that another geospatial software tool is interfering with pfdf's backend. Try installing pfdf :ref:`in a clean virtual environment <install-environment>`.


.. _faq-error-pysheds:

I'm getting errors originating from pysheds
-------------------------------------------
This may indicate that pysheds has issued a new release that breaks backwards compatibility. Try :ref:`installing pfdf from lock <install-lock>`.

