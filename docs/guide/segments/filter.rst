Filtering
=========
It's often useful to reduce a stream segment network to a subset of its segments. Typically, this is to select model-worthy segments from an initial network. The Segments class includes 3 methods to help filter networks: :ref:`remove`, :ref:`keep`, and :ref:`copy`.


.. _remove:

remove
------
The :ref:`remove <pfdf.segments.Segments.remove>` method will attempt to remove indicated segments from the network. You can indicate segments using either segment IDs, or a logical array with one element per segment in the network. For example::
    
    # Indicate segments using integer IDs
    >>> segments.remove(ids=[1,4,17,200])

    # Indicate segments using boolean indexing
    >>> areas = segments.area()
    >>> too_small = areas < 100
    >>> segments.remove(indices=too_small)
    

.. _flow-continuity:

In its default configuration, the command will prioritize flow continuity over removing segments. Thus, the command may still retain some of the indicated segments in the network. Specifically, an indicated segment will not be removed if it's between two segments being retained. For example, consider the following network:


.. figure:: /images/guide/initial-network.svg
  :alt: A stream segment network shows several segments marked for removal: segments 1 and 2 are at the top of the network, segment 4 is in the middle of the network, and segments 7 and 9 are at the bottom of the network.

  An example stream segment network.


In this example, the red segments (1, 2, 4, 7, 9) have been marked for removal. However, calling::

    >>> segments.remove(ids=[1,2,4,7,9])

would result in the following network:

.. figure:: /images/guide/remove-flow.svg
  :alt: The segments at the top of the network (1 and 2) were removed, as were the segments at the bottom (7 and 9). However, segment 4 (in the middle of the network) was not removed.

  Removal that preserves flow continuity


::

  >>> segments.ids
  array([3, 4, 5, 6, 8])

where the grey (dotted) segments have been removed, and the blue (solid) segments were retained. Note that segment 4 was not removed, even though it was included in the call to ``remove``. This segment was retained because it is bracketed by segments 3 and 6, which were retained. Removing segment 4 would thus break flow continuity, and so the segment was not removed.

Since :ref:`remove <pfdf.segments.Segments.remove>` does not necessarily remove all indicated segments, the method returns a 1D boolean array indicating the segments that were actually removed. The array will have one element per segment in the unfiltered network, and True elements indicate removal. For example, we could use::

    >>> initial_ids = segments.ids
    >>> initial_ids
    array([1, 2, 3, 4, 5, 6, 7, 8, 9])

    >>> removed = segments.remove(ids=[1,2,4,7,9])
    >>> initial_ids[removed]
    array([1, 2, 7, 9])
    >>> initial_ids[~removed]
    array([3, 4, 5, 6, 8])

to see which segments were retained and removed.

If you don't want to preserve flow-continuity, you can disable this behavior by setting the ``continuous`` option to False. For example::

    >>> removed = segments.remove(ids=[1,2,4,7,9], continuous=False)

would instead result in the following network:

.. figure:: /images/guide/remove-noflow.svg
  :alt: All of the marked segments were removed, including segment 4 in the middle of the network.

  Removal that ignores flow continuity


:: 

  >>> ids[removed]
  array([1, 2, 4, 7, 9])
  >>> ids[~removed]
  array([3, 5, 6, 8])

in which all indicated segments, including segment 4, have been removed.


.. _keep:

keep
----
The :ref:`keep <pfdf.segments.Segments.keep>` method is essentially the inverse of :ref:`remove`. This method will keep the indicated segments, and will attempt to discard all others. As with ``remove``, the command will prioritize flow continuity, so returns a 1D boolean array indicated the actions of the operation. However, True elements in this array indicated segments that were retained, rather than removed. You can also disable the preservation of flow-continuity setting ``continuous`` to False. Returning to the previous example::

    # Would not remove segment 4
    >>> kept = segments.keep(ids=[3, 5, 6, 8])
    >>> ids[kept]
    array([3, 4, 5, 6, 8])

    # Would break continuity and remove segment 4
    >>> kept = segments.keep(ids=[3, 5, 6, 8], continuous=False)
    >>> ids[kept]
    array([3, 5, 6, 8])


.. _copy:

copy
----

The :ref:`keep` and :ref:`remove` methods permanently alter a Segments object, and discarded segments cannot be restored. However, you can use the :ref:`copy <pfdf.segments.Segments.copy>` method to create a copy of the object before filtering. You can then remove segments from one copy without affecting the other. This can be useful for testing different filtering criteria::

  >>> acopy = segments.copy()
  >>> test1 = segments.area() < 100
  >>> test2 = segments.area() < 200

  >>> segments.remove(indices=test1)
  >>> acopy.remove(indices=test2)



Filtering Effects
-----------------

When segments are removed, they are permanently deleted from the Segments object. Any new statistical summaries or physical variables will only be calculated for the remaining segments. Similarly, object properties won't contain values for the deleted segments, and the outputs of the :doc:`raster <rasters>` method will only include the remaining segments. Note that a stream segment's ID is not affected by segment removal. Although an ID may be removed from the network, the individual IDs are constant, so are not renumbered when the network becomes smaller.

