=============================
Explanation of Graph Page
=============================

The graph page displays the current user's nearest neighbors.
Two options are available:

- **Graph of Like Neighbors**: plots the graph of the nearest neighbors who liked the same recipes as the current user.
- **Graph of Dislike Neighbors**: plots the graph of the nearest neighbors who disliked the same recipes as the current user.

The nearest neighbors are fixed and do not depend on the type of graph selected. 

The nearest neighbors are computed during the recipe suggestion function call (see `algorithm for recipe suggestion`_).

It may then happen that all nearest neighbors have only likes (or dislikes) in common with the current user, making one of the graphs empty.

The graph is interactive and can be moved. A list of nearest neighbors is displayed on the side, including their user_id, the number of common likes and dislikes with the current user, and the number of recipes they can still recommend.

.. _algorithm for recipe suggestion: algo_recipe_suggestion.html