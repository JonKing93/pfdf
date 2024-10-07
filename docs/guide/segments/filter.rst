Filtering
=========
It's often useful to reduce a stream segment network to a subset of its segments. Typically, this is to select model-worthy segments from an initial network. The *Segments* class includes 4 methods to help filter networks: :ref:`remove <pfdf.segments.Segments.remove>`, :ref:`keep <pfdf.segments.Segments.keep>`, :ref:`continuous <pfdf.segments.Segments.continuous>`, and :ref:`copy <pfdf.segments.Segments.copy>`.


.. _remove:

remove
------
The :ref:`remove <pfdf.segments.Segments.remove>` method will remove the selected segments from the network. By default, the command expects a boolean vector with one element per segment in the network, but you can also use the ``type`` option to select segments using IDs instead. For example:

.. code:: pycon

    >>> # Indicate segments using boolean indexing
    >>> areas = segments.area()
    >>> too_small = areas < 0.25
    >>> segments.remove(too_small)
    >>> segments.size
    954
    
    >>> # Indicate segments using integer IDs
    >>> segments.size
    1000
    >>> segments.remove([1,4,17,200], type="ids")
    >>> segments.size
    996




.. _keep:

keep
----
The :ref:`keep <pfdf.segments.Segments.keep>` method is essentially the inverse of :ref:`remove`. This method will keep the indicated segments, and will discard all others. For example:

.. code:: pycon

    >>> # Indicate segments using boolean indexing
    >>> areas = segments.area()
    [20, 250, 400, 19]
    >>> large_enough = areas > 100
    >>> segments.keep(large_enough)
    >>> segments.size
    2

    >>> # Indicate segments using integer IDs
    >>> segments.size
    1000
    >>> segments.keep([1,4,17,200], type="ids")
    >>> segments.size
    4



.. _flow-continuity:

Flow Continuity
---------------

It's often useful to filter a network in a way that preserves flow continuity. When preserving flow continuity, segments are not removed from the network when they are between two segments being retained. This ensures that the connectivity of segments in the network is not disrupted.

For example, consider the following network:

.. figure:: /images/guide/initial-network.svg
  :alt: A stream segment network shows several segments marked for removal: segments 1 and 2 are at the top of the network, segment 4 is in the middle of the network, and segments 7 and 9 are at the bottom of the network.

  An example stream segment network.

In this example, the red segments (1, 2, 4, 7, 9) have been marked for removal. However, since segment 3 flows into segment 6 via segment 4, removing segment 4 would result in a flow discontinuity. As such, it may be preferable to retain segment 4 in the network, and only discard segments 1, 2, 7, and 9. The filtered network would resemble the following:

.. figure:: /images/guide/remove-flow.svg
  :alt: The segments at the top of the network (1 and 2) were removed, as were the segments at the bottom (7 and 9). However, segment 4 (in the middle of the network) was not removed.

  Removal that preserves flow continuity

You can implement flow continuous filtering using the :ref:`continuous <pfdf.segments.Segments.continuous>` method. Given a set of segments selected for filtering, the command returns the indices of segments that can be filtered without altering flow continuity. By default, the command assumes you are filtering using the :ref:`keep command <keep>`, but you can set ``remove=True`` to indicate filtering using the :ref:`remove command <remove>` instead. As with the filtering commands, you can indicate selected segments using a boolean vector (default), or using segment IDs (with the ``type="ids" option)``. For example:

.. code:: pycon

    >>> # Filtering with "keep" and segment IDs
    >>> segments.size
    9
    >>> keep = segments.continuous([3, 5, 6, 8], type="ids")
    >>> segments.ids[keep]
    [3, 4, 5, 6, 8]

    >>> # Filtering with "remove" and segment indices
    >>> segments.size
    9
    >>> remove = np.isin(segments.ids, [1,2,4,7,9])
    >>> remove = segments.continuous(remove, remove=True)
    >>> segments.ids[remove]
    [1,2,7,9]

You can then call the :ref:`keep <keep>` or :ref:`remove <remove>` on the output indices to implement flow-continuous filtering::

    # Filtering with "keep"
    keep = segments.continuous(keep)
    segments.keep(keep)

    # Filtering with "remove"
    remove = segments.continuous(remove, remove=True)
    segments.remove(remove)




.. _nested:

Nested Basins
-------------

It is sometimes desirable to remove nested drainages from the stream segment network. A nested drainage network is a local drainage network upstream of another local drainage network, and is indicative of a flow discontinuity. Nested networks are often removed to provide cleaner :doc:`export <export>` of basin outlet points, as a nested network will result in a "hanging" outlet point in the middle of a larger drainage basin. You can locate nested segments using the :ref:`isnested command <pfdf.segments.Segments.isnested>`::

    nested = segments.isnested()

And remove them using the usual :ref:`remove command <remove>`::

    segments.remove(indices=nested)

.. tip::

    It is most common to remove nested drainages *after* exporting segments, but *before* basins and outlets. This is to preserve the nested segments in the overall hazard assessment, but to remove the possibility of "hanging" outlet points.


.. _copy:

copy
----

The :ref:`keep` and :ref:`remove` methods permanently alter a *Segments* object, and discarded segments cannot be restored. However, you can use the :ref:`copy <pfdf.segments.Segments.copy>` method to create a copy of the object before filtering. You can then remove segments from one copy without affecting the other. This can be useful for testing different filtering criteria::

  # Copy the segments and create two different filtering criteria
  acopy = segments.copy()
  test1 = segments.area() < 100
  test2 = segments.area() < 200

  # Filter the segments and the copy using separate criteria
  segments.remove(indices=test1)
  acopy.remove(indices=test2)


Filtering Effects
-----------------

When segments are removed, they are permanently deleted from the *Segments* object. Any new statistical summaries or physical variables will only be calculated for the remaining segments. Similarly, object properties won't contain values for the deleted segments, and the outputs of the :doc:`raster <rasters>` method will only include the remaining segments. Note that a stream segment's ID is not affected by segment removal. Although an ID may be removed from the network, the individual IDs are constant, so are not renumbered when the network becomes smaller.

Finally, note that removing a terminal segment will delete any previously saved basins raster. As such, we recommend only calling the :ref:`locate_basins method <pfdf.segments.Segments.locate_basins>` *after* filtering.