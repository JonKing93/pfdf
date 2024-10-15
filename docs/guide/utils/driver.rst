File driver info
================

The :ref:`utils.driver module <pfdf.utils.driver>` provides information about supported vector and raster file formats. 


.. _raster-drivers:

Raster Formats
--------------
The :ref:`rasters <pfdf.utils.driver.rasters>` function returns a summary of supported raster file drivers:

.. code:: pycon

    >>> from pfdf.utils import driver
    >>> driver.rasters()
                                               Description        Extensions
    ADRG                ADRG/ARC Digitized Raster Graphics              .gen
    BMP                                             Bitmap              .bmp
    BT                           VTP Binary Terrain Format               .bt
    BYN       Natural Resources Canada's Geoid file format        .byn, .err
    EHdr                                 ESRI labelled hdr              .bil
    ERS                                           ERMapper              .ers
    GTiff                              GeoTIFF File Format       .tif, .tiff
    HFA                                      Erdas Imagine              .img
    ILWIS                                       Raster Map        .mpr, .mpl
    ISIS3          USGS Astrogeology ISIS Cube (Version 3)        .lbl, .cub
    KRO                                   KOLOR Raw Format              .kro
    MFF                                  Vexcel MFF Raster              .hdr
    NITF              National Imagery Transmission Format              .ntf
    NTv2                             NTv2 Datum Grid Shift        .gsb, .gvb
    NWT_GRD          Northwood/Vertical Mapper File Format              .grd
    PCIDSK                     PCI Geomatics Database File              .pix
    PCRaster                   PCRaster raster file format              .map
    PDS4            NASA Planetary Data System (Version 4)              .xml
    RMF                               Raster Matrix Format              .rsw
    SAGA                  SAGA GIS Binary Grid File Format  .sdat, .sg-grd-z
    SGI                                   SGI Image Format              .rgb
    Terragen                         Terragen Terrain File              .ter
    USGSDEM                      USGS ASCII DEM (and CDED)              .dem
    VRT                                GDAL Virtual Format              .vrt

.. _vector-drivers:

Vector Formats
--------------
And the :ref:`vectors <pfdf.utils.driver.vectors>` function returns the supported vector file formats:

.. code:: pycon

    >>> driver.vectors()
                                   Description                  Extensions
    CSV                  Comma Separated Value                        .csv
    DGN                       Microstation DGN                        .dgn
    DXF                            AutoCAD DXF                        .dxf
    FlatGeobuf                      FlatGeobuf                        .fgb
    GML              Geography Markup Language                  .gml, .xml
    GPKG                     GeoPackage vector                       .gpkg
    GPX                    GPS Exchange Format                        .gpx
    GeoJSON                            GeoJSON             .json, .geojson
    GeoJSONSeq    Sequence of GeoJSON features        .geojsons, .geojsonl
    MapInfo File       MapInfo TAB and MIF/MID            .tab, .mid, .mif
    OGR_GMT                  GMT ASCII Vectors                        .gmt
    OpenFileGDB   ESRI File Geodatabase Vector                        .gdb
    Shapefile             ESRI Shapefile / DBF  .shp, .dbf, .shz, .shp.zip
    SQLite           SQLite / Spatialite RDBMS                .sqlite, .db


Extensions
----------

Alternatively, you can use the :ref:`extensions <pfdf.utils.driver.extensions>` function to see the file format inferred by various extensions:

.. code:: pycon

    >>> driver.extensions(type="raster")
                 Driver                                   Description
    .bil           EHdr                             ESRI labelled hdr
    .bmp            BMP                                        Bitmap
    .bt              BT                     VTP Binary Terrain Format
    .byn            BYN  Natural Resources Canada's Geoid file format
    .cub          ISIS3       USGS Astrogeology ISIS Cube (Version 3)
    .dem        USGSDEM                     USGS ASCII DEM (and CDED)
    .err            BYN  Natural Resources Canada's Geoid file format
    .ers            ERS                                      ERMapper
    .gen           ADRG            ADRG/ARC Digitized Raster Graphics
    .grd        NWT_GRD         Northwood/Vertical Mapper File Format
    .gsb           NTv2                         NTv2 Datum Grid Shift
    .gvb           NTv2                         NTv2 Datum Grid Shift
    .hdr            MFF                             Vexcel MFF Raster
    .img            HFA                                 Erdas Imagine
    .kro            KRO                              KOLOR Raw Format
    .lbl          ISIS3       USGS Astrogeology ISIS Cube (Version 3)
    .map       PCRaster                   PCRaster raster file format
    .mpl          ILWIS                                    Raster Map
    .mpr          ILWIS                                    Raster Map
    .ntf           NITF          National Imagery Transmission Format
    .pix         PCIDSK                   PCI Geomatics Database File
    .rgb            SGI                              SGI Image Format
    .rsw            RMF                          Raster Matrix Format
    .sdat          SAGA              SAGA GIS Binary Grid File Format
    .sg-grd-z      SAGA              SAGA GIS Binary Grid File Format
    .ter       Terragen                         Terragen Terrain File
    .tif          GTiff                           GeoTIFF File Format
    .tiff         GTiff                           GeoTIFF File Format
    .vrt            VRT                           GDAL Virtual Format
    .xml           PDS4        NASA Planetary Data System (Version 4)

.. code:: pycon

    >>> driver.extensions(type="vector")
                     Driver                   Description
    .csv                CSV         Comma Separated Value
    .db              SQLite     SQLite / Spatialite RDBMS
    .dbf          Shapefile          ESRI Shapefile / DBF
    .dgn                DGN              Microstation DGN
    .dxf                DXF                   AutoCAD DXF
    .fgb         FlatGeobuf                    FlatGeobuf
    .gdb        OpenFileGDB  ESRI File Geodatabase Vector
    .geojson        GeoJSON                       GeoJSON
    .geojsonl    GeoJSONSeq  Sequence of GeoJSON features
    .geojsons    GeoJSONSeq  Sequence of GeoJSON features
    .gml                GML     Geography Markup Language
    .gmt            OGR_GMT             GMT ASCII Vectors
    .gpkg              GPKG             GeoPackage vector
    .gpx                GPX           GPS Exchange Format
    .json           GeoJSON                       GeoJSON
    .mid       MapInfo File       MapInfo TAB and MIF/MID
    .mif       MapInfo File       MapInfo TAB and MIF/MID
    .shp          Shapefile          ESRI Shapefile / DBF
    .shp.zip      Shapefile          ESRI Shapefile / DBF
    .shz          Shapefile          ESRI Shapefile / DBF
    .sqlite          SQLite     SQLite / Spatialite RDBMS
    .tab       MapInfo File       MapInfo TAB and MIF/MID
    .xml                GML     Geography Markup Language