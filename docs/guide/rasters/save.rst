Saving Rasters
==============

All pfdf commands that produce a raster will return a *Raster* object as output. You can use the ``values`` property to retrieve the raster's data grid, but it's often useful to use the :ref:`save method <pfdf.raster.Raster.save>` to save the raster to the indicated filepath::

    # Save to file
    path = raster.save('my-file.tif')

By default, this method will not overwrite existing files, but you can use the ``overwrite`` option to change this::

    # Save to file and overwrite any existing file
    path = raster.save('my-file.tif', overwrite=True)

You can also use the ``driver`` option to specify the file format for filepaths with non-standard extensions::

    # Save a GeoTiff with an unusual extension
    path = raster.save('my-file.unusual', driver='GTiff')