models.cannon2010 module
========================

.. _pfdf.models.cannon2010:

.. py:module:: pfdf.models.cannon2010

    Implements a combined hazard (likelihood + volume) assessment model

    .. list-table::
        :header-rows: 1

        * - Function
          - Description
        * - :ref:`hazard <pfdf.models.cannon2010.hazard>`
          - Determines the combined relative hazard classes for a set of debris flows
        * - :ref:`pscore <pfdf.models.cannon2010.pscore>`
          - Returns the classification score for debris flow likelihoods
        * - :ref:`vscore <pfdf.models.cannon2010.vscore>`
          - Returns the classification score for debris flow sediment volumes
        * - :ref:`hscore <pfdf.models.cannon2010.hscore>`
          - Returns the combined hazard class given combined hazard scores


    
    This module implements the combined relative hazard classification model presented in `Cannon et al., 2010 <https://doi.org/10.1130/B26459.1>`_. This model classifies debris-flow hazard by by considering both likelihood and potential sediment volume. In brief, the model classifies likelihood and volume hazards separately, and assigned a score to each class. These two scores are then added, and the combined score determines the final combined-hazard class.

    Workflow
    --------

    Most users will want to start with the :ref:`hazard <pfdf.models.cannon2010.hazard>` function. This function returns combined relative hazard classes for a set of debris flows, given the debris flow likelihoods and potential sediment volumes. Note that you can use the :ref:`staley2017 <pfdf.models.staley2017>` module to compute likelihoods, and the :ref:`gartner2014 <pfdf.models.gartner2014>` module to compute volumes, although the use of these modules is not strictly required.

    Advanced users may be interested in the :ref:`pscore <pfdf.models.cannon2010.pscore>`, :ref:`vscore <pfdf.models.cannon2010.vscore>`, and :ref:`hscore <pfdf.models.cannon2010.hscore>` functions, which calculate the individual (p)robability, (v)olume, and (h)azard scores. Some users may also be interested in changing the model configuration to implement custom hazard assessment thresholds. You can do so by providing the optional "thresholds" argument to any function.

    Thresholds
    ----------

    .. _c10-default-thresholds:

    The following table summarizes the default model thresholds, as presented in the paper:

    =====  ===========  ============  ======
    Class  Probability  Volume        Hazard
    =====  ===========  ============  ======
    1      [0, 0.25]    [0, 10^3]     1 - 3
    2      (0.25, 0.5]  (10^3, 10^4]  4 - 6
    3      (0.5, 0.75]  (10^4, 10^5]  > 7
    4      (0.75, 1]    > 10^5        N/A
    =====  ===========  ============  ======

    When providing custom thresholds for any portion of the analysis, the thresholds should be a vector of N increasing values, such that thresholds = :math:`[T_1, \ T_2, \ ..., \ T_n]`. Then, the relevant scores are assigned as follows:

    ========================  =====
    Values                    Score
    ========================  =====
    :math:`[0, \ T_1]`        1
    :math:`(T_1, \ T_2]`      2
    ...                       ...
    :math:`(T_{n-1}, \ T_n]`  N
    :math:`(T_n, \ ∞]`        N+1
    ========================  =====

----

.. _broadcastable: https://numpy.org/doc/stable/user/basics.broadcasting.html


.. _pfdf.models.cannon2010.hazard:

.. py:function:: hazard(likelihoods, volumes, *, p_thresholds = [0.25, 0.5, 0.75], v_thresholds = [1e3, 1e4, 1e5], h_thresholds = [3, 6])
    :module: pfdf.models.cannon2010

    Computes the combined relative hazard scores for a set of debris flows

    .. dropdown:: Classify Hazard

        ::

            hazard(likelihoods, volumes)

        Computes combined relative hazard classes, given a set of debris flow likelihoods and potential sediment volumes (meters^3). The shapes of the likelihood and volume arrays must be `broadcastable`_.

    .. dropdown:: Custom Thresholds

        ::     

            hazard(..., *, p_thresholds)
            hazard(..., *, v_thresholds)
            hazard(..., *, h_thresholds)

    
        Specify custom thresholds for the (p)robability, (v)olume, and (h)azard classification scores. Each set of thresholds must be a set of N positive values in an increasing order. Note that N defines the number of breakpoints, so the number of classifications will be N+1. Elements of p_thresholds must be on the interval from 0 to 1, v_thresholds must be positive, and h_thresholds must be positive integers.

        .. note:: Specifying v_thresholds relaxes the unit requirements for the input sediment volumes. When this is the case, v_thresholds and volumes must use the same units, but any units are permitted.

    :Inputs: * **likelihoods** (*ndarray*) -- An array of debris flow likelihoods. Values should be on the interval from 0 to 1.
             * **volumes** (*ndarray*) -- An array of debris flow volumes. If not specifying v_thresholds, then units should be meters^3. Otherwise, units should be the same as v_thresholds. The shape of this array must be `broadcastable`_ with the likelihoods array.
             * **p_thresholds** (*vector*) -- Custom thresholds for the likelihood scores. Elements must be on the interval 0 to 1, in ascending order.
             * **v_thresholds** (*vector*) -- Custom thresholds for the volume scores. Elements must be positive values, in ascending order.
             * **h_thresholds** (*vector*) -- Custom thresholds for the combined hazard classification. Elements must be positive integers, in ascending order.

    :Outputs: *ndarray* -- The combined relative hazard classifications for the debris flows. The shape of this array is the shape obtained by broadcasting the likelihood scores with the volume scores.

    
.. _pfdf.models.cannon2010.pscore:

.. py:function:: pscore(likelihoods, thresholds = [0.25, 0.5, 0.75])
    :module: pfdf.models.cannon2010

    Scores a set of debris flow likelihoods

    .. dropdown:: Classify likelihoods

        ::

            pscore(likelihoods)
            
        Returns the classification scores for a set of debris flow likelihoods, using the :ref:`default thresholds <c10-default-thresholds>`. 
        
        .. note:: Probabilities should be on the interval from 0 to 1.


    .. dropdown:: Custom Thresholds

        ::

            pscore(likelihoods, thresholds)

        Specifies the thresholds used to score the likelihoods. The "thresholds" input should be a vector of N increasing values on the interval from 0 to 1. Each element is the dividing point between two scores. 
        
        .. note:: N is the number of breakpoints, so the number of classification groups will be N+1.

    :Inputs: * **likelihoods** (*ndarray*) -- An array of debris flow likelihoods. Values should be on the interval from 0 to 1. NaN values are allowed and are given a score of NaN.
            * **thresholds** (*vector*) -- The likelihood thresholds to use for scoring. Must be a vector of increasing values on the interval from 0 to 1.

    :Outputs: *ndarray* -- The scores for the debris-flow likelihoods


.. _pfdf.models.cannon2010.vscore:

.. py:function:: vscore(volumes, thresholds = [1e3, 1e4, 1e5])
    :module: pfdf.models.cannon2010

    Scores a set of debris flow sediment volumes

    .. dropdown:: Classify Volumes

        ::

            vscore(volumes)

        Returns the classification scores for a set of debris flow sediment volumes (in units of meters^3) using the :ref:`default thresholds <c10-default-thresholds>`.

    .. dropdown:: Custom Thresholds

        ::

            vscore(volumes, thresholds)

        Specifies the thresholds to use for classifying debris flow sediment volumes. Each element in thresholds is the dividing point between two scores. The "thresholds" input should be a vector of N positive values in increasing order. Each element is the dividing point between two scores. 
        
        .. note:: N is the number of breakpoints, so the number of classification groups will be N+1.

    :Inputs: * **volumes** (*ndarray*) -- An array of potential debris-flow sediment volumes. If specifying thresholds, should use the same units as the thresholds. Otherwise, units should be meters^3. NaN values are allowed and are given a score of NaN.
             * **thresholds** (*vector*) -- The thresholds to use for classifying debris flow volumes. Must use the same units as the volumes.

    :Outputs: *ndarray* -- The classification scores of the debris flow volumes



.. _pfdf.models.cannon2010.hscore:

.. py:function:: hscore(combined, thresholds = [3, 6])
    :module: pfdf.models.cannon2010

    Computes a combined hazard assessment score

    .. dropdown:: Classify Hazards

        ::

            hscore(combined)

        Classifies debris-flow hazard using the combined likelihood and volume classification scores (i.e. combined = pscore + vscore). Uses the :ref:`default thresholds <c10-default-thresholds>`.


    .. dropdown:: Custom Thresholds

        ::

            hscore(combined, thresholds)

        Specifies the thresholds to use for classifying debris flow hazards. Each element in thresholds is the dividing point between two classes. The "thresholds" input should be a vector of N positive integers, in increasing order. Each element is the dividing point between two scores. 
        
        .. note:: N is the number of breakpoints, so the number of classification groups will be N+1.

    :Inputs: * **combined** (*ndarray*) -- The combined relative hazard scores. This is the sum of the classification scores for likelihood and volume. NaN values are allowed and will receive a hazard class of NaN.
             * **thresholds** (*vector*) -- The thresholds to use to determine hazard classes. Should be a vector of N positive integers in ascending order.

    :Outputs: *ndarray* -- The combined hazard classifications

