=============================
Explanation of Recipe Suggestion
=============================

Example Context
----------------------
**User X** has rated 2 recipes:

- Recipe 1: ``+1``
- Recipe 2: ``-1``

The interaction data includes several recipes not yet rated by **User X**: ``[3, 4, 5, 6]``.

A new user, **User X'**, is added and rates the recipes ``[1, 2]`` with the same ratings as **User X**.

Interactions of other users:

.. list-table::
   :header-rows: 1

   * - user_id
     - recipe_id
     - rating
   * - 1
     - 1
     - +1
   * - 1
     - 2
     - 0
   * - 1
     - 4
     - +1
   * - 1
     - 5
     - +1
   * - 2
     - 1
     - -1
   * - 2
     - 3
     - +1
   * - 2
     - 4
     - 0
   * - 2
     - 6
     - -1
   * - 3
     - 2
     - -1
   * - 3
     - 3
     - +1
   * - 3
     - 5
     - +1
   * - X'
     - 1
     - +1
   * - X'
     - 2
     - -1


Algorithm Steps
-----------------------

**Step 1: Preferences of User X**

**User X** has rated the following recipes:

- Recipe 1: ``+1``
- Recipe 2: ``-1``

This means that **User X** has not yet rated recipes ``[3, 4, 5, 6]``.

**Step 2: Pivot Table**

We filter the interactions of other users to keep only recipes ``[1, 2]`` (those already rated by **User X**). Then, we build a pivot table.

Filtered data:

.. list-table::
   :header-rows: 1

   * - user_id
     - recipe_id
     - rating
   * - 1
     - 1
     - +1
   * - 1
     - 2
     - 0
   * - 2
     - 1
     - -1
   * - 3
     - 2
     - -1
   * - X'
     - 1
     - +1
   * - X'
     - 2
     - -1

Pivot Table:

.. list-table::
   :header-rows: 1

   * - user_id
     - Recipe 1
     - Recipe 2
   * - 1
     - +1
     - 0
   * - 2
     - -1
     - 0
   * - 3
     - 0
     - -1
   * - X'
     - +1
     - -1

**Step 3: Absolute Deviation Calculation**

The ``abs_deviation`` method is used to compute the absolute deviation between **User X**'s preferences (``[+1, -1]``) and other users' ratings.

User Preferences:

- Recipe 1: ``+1``
- Recipe 2: ``-1``

Distance Calculation:

.. list-table::
   :header-rows: 1

   * - user_id
     - Recipe 1
     - Recipe 2
     - Total Distance
   * - 1
     - 0
     - 1
     - 1
   * - 2
     - 2
     - 1
     - 3
   * - 3
     - 1
     - 0
     - 1
   * - X'
     - 0
     - 0
     - 0

The closest users (those with the smallest distances) are **User 1**, **User 3**, and **User X'**. However, **User X'** will be excluded because they have not rated recipes that **User X** has not yet rated.

**Step 4: Identification of Close Neighbors**

The ``near_neighboor`` method filters the interactions of close users to keep only recipes not yet rated by **User X** (``[3, 4, 5, 6]``).

Data of close neighbors:

.. list-table::
   :header-rows: 1

   * - user_id
     - recipe_id
     - rating
   * - 1
     - 4
     - +1
   * - 1
     - 5
     - +1
   * - 3
     - 3
     - +1
   * - 3
     - 5
     - +1

Note: **User X'** interactions are excluded because they have not rated any new recipes.

**Step 5: Suggesting a Recipe**

We aggregate the evaluations of neighbors for the remaining recipes (``[3, 4, 5, 6]``) and select the one with the highest score.

Recipe Scores:

.. list-table::
   :header-rows: 1

   * - Recipe
     - Total Score
   * - 3
     - +1 (User 3)
   * - 4
     - +1 (User 1)
   * - 5
     - +1 (User 1) + +1 (User 3) = +2
   * - 6
     - 0

**Suggested Recipe:**

Recipe 5 is suggested because it has the highest score.

