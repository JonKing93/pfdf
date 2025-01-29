"""
Type aliases for the post-wildfire debris-flow package
----------
The typing subpackage holds modules with type aliases used across multiple modules in
the pfdf package. Note that these modules do not provide *every* type alias used within
the package. Rather, they provides common aliases that are across multiple modules. As
such, individual modules may still define aliases unique to their implementations.
----------
Modules:
    core        - Low level type hints viable anywhere in the package
    raster      - Type hints derived from the Raster class
    segments    - Type hints for Segments objects and their outputs
    models      - Type hints for models
"""
