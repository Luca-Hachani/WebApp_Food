"""
Module containing the User class for recipe recommendations.
"""
# Importation des librairies
from dataclasses import dataclass, field
from webapp_food.utils import NoNeighborError
import numpy as np
import pandas as pd
import networkx as nx
import logging
from webapp_food.settings import LIKE, DISLIKE, \
    USER_COLUMNS, USER_MAIN_DF, USER_DESSERT_DF, \
    TYPE_OF_DISH, NEIGHBOR_DATA

logger = logging.getLogger(__name__)


@dataclass
class User:
    """
    Class representing a user and their interactions with recipes,
    particularly for suggesting recipes based on their preferences.

    Attributes
    ----------
    __type_of_dish : str
        The preferred type of dish for the user (must be "main" or "dessert").

    __preferences : dict
        A dictionary containing the user's preferences,
        where the keys are recipe IDs and the values are the ratings given
        (default: empty dictionary).

    __interactions_main : pd.DataFrame
        Dataset containing user-recipe interactions for main dishes
        (dynamically loaded).

    __interactions_dessert : pd.DataFrame
        Dataset containing user-recipe interactions for desserts
        (dynamically loaded).

    __near_neighbor : pd.DataFrame
        DataFrame containing the user IDs of nearby users.

    Methods
    -------
    __init__(type_of_dish: str, test: bool = False,
            df_main: pd.DataFrame = None,
            df_dessert: pd.DataFrame = None) -> None
        Initializes a new user with a preferred type of dish and optionally
        loads test datasets.

    validity_type_of_dish(type_of_dish: str) -> None
        Checks if the dish type is valid ("main" or "dessert").
        Raises an error if invalid.

    pivot_table_of_df(interactions_reduce: pd.DataFrame) -> pd.DataFrame
        Converts a DataFrame of interactions into a pivot table with user IDs
        as rows and recipe IDs as columns.

    abs_deviation(recipes_rating: np.ndarray,
    interactions_pivot: pd.DataFrame) -> pd.DataFrame
        Calculates the absolute deviation between recipe ratings and
        existing interactions.

    def percentile_filter(interactions_pivot: pd.DataFrame,
                          nb_filtered_rows_min: int=5,
                          nb_filtered_rows_max: int=100):
        Filters a DataFrame of user-recipe interactions based on
        the 10th percentile of a "dist" column, with constraints on
        the minimum and maximum number of rows.

    load_datasets() -> None
        Loads datasets for main dishes and desserts, if not already loaded.

    get_type_of_dish() -> str
        Returns the user's preferred type of dish.

    get_preferences() -> dict
        Returns the user's preferences dictionary.

    get_interactions() -> pd.DataFrame
        Returns the dataset of user-recipe interactions for the current type
        of dish.

    get_near_neighbor() -> pd.DataFrame
        Returns the DataFrame of near neighbors.

    near_neighbor(recipes_id: list, recipes_rating: np.ndarray,
                  interactions: pd.DataFrame,
                  interactions_pivot_input: pd.DataFrame) -> pd.DataFrame
    Selects close neighbor users based on their distances
    and interactions.

    recipe_suggestion() -> int
        Suggests a recipe based on the user's preferences and existing
        interactions. If no preferences exist, a random recipe is suggested.

    add_preferences(recipe_suggested: int, rating: int) -> None
        Adds a preference for a specific recipe with a given rating.

    del_preferences(recipe_deleted: int) -> None
        Removes a preference associated with a specific recipe.

    get_graph(type: int) -> nx.MultiGraph
        Generates a user interaction graph based on preferences and recipes.

    get_neighbor_data(type: int) -> pd.DataFrame
        Analyzes interactions between the main user and their close neighbors
        to identify commonly liked recipes, commonly disliked recipes, and
        recipes to recommend.

    Notes
    -----
    - Interactions are stored in CSV files, loaded at runtime.
    - The `recipe_suggestion` method implements a simple recommendation system
      based on user similarity using absolute distances.

    Example
    -------
    #1 Create a user for main dishes :
    user = User(type_of_dish="main")

    #2 Suggest a recipe :
    suggestion = user.recipe_suggestion()

    #3 Add a preference :
    user.add_preferences(recipe_suggested=123, rating=+1/-1)

    #4 Remove a preference :
    user.del_preferences(recipe_deleted=123)
    """

    __type_of_dish: str
    __preferences: dict = field(default_factory=dict)
    __interactions_main: pd.DataFrame = field(
        init=False, repr=False)
    __interactions_dessert: pd.DataFrame = field(
        init=False, repr=False)
    __near_neighbor: pd.DataFrame = field(
        init=False, repr=False)

    # init

    def __init__(self, type_of_dish: str, test: bool = False,
                 df_main: pd.DataFrame = None,
                 df_dessert: pd.DataFrame = None)\
            -> None:
        """
        Initializes a new user with a preferred type of dish.

        Parameters
        ----------
        type_of_dish : str
            The preferred type of dish for the user ("main" or "dessert").

        Raises
        ------
        ValueError
            If the dish type is invalid.
        """
        logger.debug(f"Creating a new user for {type_of_dish} dishes")
        self.__type_of_dish = type_of_dish
        self.__preferences = {}
        # Test dish type validity
        self.validity_type_of_dish(self.get_type_of_dish)
        # Load the datasets only once to avoid unnecessary overhead.
        if not test:
            self.load_datasets()
        else:
            self.__interactions_main = df_main
            self.__interactions_dessert = df_dessert
        # Initialise near neighbors at None
        self.__near_neighbor = pd.DataFrame()

    # static methods

    @staticmethod
    def validity_type_of_dish(type_of_dish: str) -> None:
        """
        Validates the dish type.

        Parameters
        ----------
        type_of_dish : str
            The provided dish type (must be "main" or "dessert").

        Raises
        ------
        ValueError
            If the dish type is neither "main" nor "dessert".
        """
        logger.debug(f"Checking validity of type_of_dish={type_of_dish}")
        if type_of_dish not in TYPE_OF_DISH:
            logger.info(f"Invalid type of dish: {type_of_dish}")
            raise ValueError(f'The type of dish must be "main" or \
                             "dessert" only, and not "{
                             type_of_dish}".')

    @staticmethod
    def pivot_table_of_df(interactions_reduce: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms a user-recipe interaction DataFrame into a pivot table.

        Parameters
        ----------
        interactions_reduce : pd.DataFrame
            Filtered interaction DataFrame containing the columns "user_id",
            "recipe_id", and "rating".

        Returns
        -------
        pd.DataFrame
            A pivot table with user IDs as rows, recipe IDs as columns, and
            ratings as values. Missing values are replaced with 0.
        """
        logger.debug("Pivoting DataFrame of interactions")
        interactions_pivot = interactions_reduce.pivot(
            index=USER_COLUMNS[0], columns=USER_COLUMNS[1],
            values=USER_COLUMNS[2])
        interactions_pivot = interactions_pivot.fillna(0)
        interactions_pivot.columns.name = None
        interactions_pivot.index.name = None
        return interactions_pivot

    @staticmethod
    def abs_deviation(recipes_rating: np.ndarray,
                      interactions_pivot: pd.DataFrame) -> pd.DataFrame:
        """
        Computes the absolute deviation between a new user's
        recipe preferences and existing interactions.

        Parameters
        ----------
        recipes_rating : np.ndarray
            Preferences assigned to recipes by the new user (1D array).
        interactions_pivot : pd.DataFrame
            Pivot table of interactions containing user ratings for
            each recipe.

        Returns
        -------
        pd.DataFrame
            DataFrame containing absolute deviations between the new user's
            preferences and existing users' preferences.
        """
        logger.debug(
            "Calculating absolute deviation between user \
            preferences and existing interactions")
        interactions_abs = np.abs(
            interactions_pivot-recipes_rating)
        return interactions_abs

    @staticmethod
    def percentile_filter(interactions_pivot: pd.DataFrame,
                          nb_filtered_rows_min: int=5,
                          nb_filtered_rows_max: int=100) \
                            -> tuple[pd.DataFrame, int]:
        """
        Filters a DataFrame of user-recipe interactions based on
        the 10th percentile of a "dist" column, with constraints on
        the minimum and maximum number of rows.

        The function applies a filter to retain rows where
        the "dist" value is less than or equal to the 10th percentile of
        the "dist" column. It ensures that the resulting filtered DataFrame
        has at least `nb_filtered_rows_min` rows and
        at most `nb_filtered_rows_max` rows.

        Parameters
        ----------
        interactions_pivot : pd.DataFrame
            The input pivot table containing a "dist" column used for
            filtering.
        nb_filtered_rows_min : int, optional
            The minimum number of rows to retain in the filtered DataFrame,
            by default 5.
        nb_filtered_rows_max : int, optional
            The maximum number of rows to retain in the filtered DataFrame,
            by default 100.

        Returns
        -------
        tuple
            A tuple containing:
            - pd.DataFrame: The filtered pivot table.
            - int: The number of rows in the filtered DataFrame.

        Notes
        -----
        - If the number of rows after filtering by the 10th percentile is less
        than `nb_filtered_rows_min`, no filtering is applied.
        - If the filtered rows exceed `nb_filtered_rows_max`,
        additional filtering is applied to meet the maximum constraint.

        Example
        -------
        >>> import pandas as pd
        >>> interactions_pivot["dist"] = [1, 2, 5, 3, 1, 8, 5, 4, 9]
        >>> filtered_df, nb_rows = percentile_filter(interactions_pivot, 2, 4)
        >>> print(filtered_df)
            dist
        0    1
        4    1
        >>> print(nb_rows)
        2
        """
        percentile_10 = interactions_pivot['dist'].quantile(0.1)
        filter_percentile_10 = interactions_pivot['dist'] <= percentile_10
        nb_filtered_rows = (filter_percentile_10).sum()
        if nb_filtered_rows < nb_filtered_rows_min:
            nb_filtered_rows = nb_filtered_rows_min
        elif nb_filtered_rows > nb_filtered_rows_max:
            nb_filtered_rows = nb_filtered_rows_max
        else:
            interactions_pivot = interactions_pivot[filter_percentile_10]
        return interactions_pivot, nb_filtered_rows

    # class methods

    @classmethod
    def load_datasets(cls) -> None:
        """
        Loads user-recipe interaction datasets for main dishes and desserts.

        Notes
        -----
        - CSV files are loaded only once at the class level.
        - Files must be located at the specified paths
          ("data/data/PP_user_main_dishes.csv" and "data/PP_user_desserts").

        """
        logger.debug("Loading datasets for main dishes and desserts")
        if not hasattr(cls, "__interactions_main") or \
                not hasattr(cls, "__interactions_dessert"):
            cls.__interactions_main = pd.read_csv(
                USER_MAIN_DF, sep=',')
            cls.__interactions_dessert = pd.read_csv(
                USER_DESSERT_DF, sep=',')

    # Getters

    @property
    def get_type_of_dish(self) -> str:
        """
        Returns the type of dish desired by the user.

        Returns
        -------
        str
            The type of dish ("main" or "dessert").
        """
        logger.debug("Getting type of dish for user")
        return self.__type_of_dish

    @property
    def get_preferences(self) -> dict:
        """
        Returns the user's preferences.

        Returns
        -------
        dict
            A dictionary where keys are recipe IDs and values are the ratings.
        """
        logger.debug("Getting preferences for user")
        return self.__preferences

    @property
    def get_interactions(self) -> pd.DataFrame:
        """
        Returns the dataset for the current type of dish.

        Returns:
        -------
        pd.DataFrame:
            Dataset of interactions.
        """
        logger.debug("Getting interactions dataset")
        if self.get_type_of_dish == TYPE_OF_DISH[0]:
            interactions = self.__interactions_main
        elif self.get_type_of_dish == TYPE_OF_DISH[1]:
            interactions = self.__interactions_dessert

        return interactions

    @property
    def get_near_neighbor(self) -> pd.DataFrame:
        """
        Returns the DataFrame of near neighbors.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the user IDs of nearby users.
        """
        logger.debug("Getting near neighbors")
        return self.__near_neighbor

    # methods

    def near_neighbor(self, recipes_id: list, recipes_rating: np.ndarray,
                      interactions: pd.DataFrame,
                      interactions_pivot_input: pd.DataFrame) -> pd.DataFrame:
        """
        Selects nearby users based on distances and their interactions.

        Parameters
        ----------
        recipes_id : list
            List of recipe IDs already reviewed by the new user.
        recipes_rating : np.ndarray
            Preferences assigned to recipes by the new user (1D array).
        interactions : pd.DataFrame
            DataFrame containing user-recipe interactions.
        interactions_pivot_input : pd.DataFrame
            Pivot table containing user distances and recipe interactions.

        Returns
        -------
        pd.DataFrame
            Filtered interactions from nearby users for recipes not reviewed
            by the new user.
        """
        logger.debug(
            "Selecting near neighbors based on distance and interactions")
        interactions_abs = self.abs_deviation(recipes_rating,
                                              interactions_pivot_input)
        interactions_pivot_input["dist"] = interactions_abs.sum(axis=1)
        interactions_pivot_input = interactions_pivot_input[
            ~np.array(np.all(interactions_abs==2, axis=1))]
        interactions_pivot_input, nb_filtered_rows = self.percentile_filter(
            interactions_pivot_input)
        user_prox_id = interactions_pivot_input.sort_values(
            "dist").head(nb_filtered_rows).index
        # sys.exit('flag')
        interactions_prox = interactions[interactions[USER_COLUMNS[0]].isin(
            user_prox_id)]
        interactions_prox = interactions_prox[
            ~interactions_prox[USER_COLUMNS[1]].isin(recipes_id)]
        interactions_pivot_output = User.pivot_table_of_df(interactions_prox)
        interactions_pivot_output = interactions_pivot_output.reindex(
            user_prox_id)
        user_prox_id = np.unique(interactions_prox[USER_COLUMNS[0]])
        interactions_selection = interactions_pivot_output.loc[user_prox_id]
        return interactions_selection

    def recipe_suggestion(self) -> int:
        """
        Suggests a recipe based on the new user's preferences and
        existing interactions.

        Returns
        -------
        int
            Suggested recipe ID.

        Notes
        -----
        - If the new user has no preferences, a random recipe is suggested.
        - The suggestion is based on the similarity of nearby users.

        """
        logger.debug("Proposing a recipe suggestion for user")
        interactions = self.get_interactions
        preferences = self.get_preferences
        if len(preferences) == 0:
            logger.info('user new historic is empty')
            recipe_suggested = interactions[
                USER_COLUMNS[1]].sample(n=1).iloc[0]
        else:
            recipes_id = list(preferences.keys())
            recipes_rating = np.array(
                list(preferences.values())).reshape(1, -1)
            interactions_reduce = interactions[
                interactions[USER_COLUMNS[1]].isin(
                    recipes_id)]
            interactions_pivot = self.pivot_table_of_df(interactions_reduce)
            interactions_selection = self.near_neighbor(recipes_id,
                                                        recipes_rating,
                                                        interactions,
                                                        interactions_pivot)
            self.__near_neighbor = interactions_selection.index
            if interactions_selection.empty:
                # drop recipes already in preferences
                interactions_selection = interactions[
                    ~interactions[USER_COLUMNS[1]].isin(recipes_id)]
                if interactions_selection.empty:
                    logger.info('No more recipes to suggest from the dataset')
                    raise ValueError('No more recipes to suggest.')
                else:
                    logger.info(
                        'No more recipes to suggest from the \
                        user preferences, suggesting a random recipe')
                    recipe_suggested = \
                        interactions_selection[
                            USER_COLUMNS[1]].sample(n=1).iloc[0]
            else:
                recipe_suggested = int(
                    interactions_selection.sum(axis=0).idxmax())
        return recipe_suggested

    def add_preferences(self, recipe_suggested: int, rating: int) -> None:
        """
        Adds a new preference for a specific recipe.

        Parameters
        ----------
        recipe_suggested : int
            The ID of the recipe to be added to preferences.
        rating : int
            The rating assigned to the recipe.
        """
        logger.debug(f"Adding a new preference for recipe {
                     recipe_suggested} with rating {rating}")
        self.__preferences[recipe_suggested] = rating

    def del_preferences(self, recipe_deleted: int) -> None:
        """
        Removes a preference associated with a specific recipe.

        Parameters
        ----------
        recipe_deleted : int
            The ID of the recipe to be removed from preferences.

        Raises
        ------
        KeyError
            If the recipe ID does not exist in the user's preferences.
        """
        logger.debug(f"Deleting preference for recipe {recipe_deleted}")
        if recipe_deleted in self.get_preferences:
            del self.__preferences[recipe_deleted]
        else:
            logger.info(f'Recipe ID {recipe_deleted} not in user preferences')
            raise KeyError(
                f'The recipe ID {recipe_deleted}\
                is not in the user preferences.')

    def get_graph(self, type: int) -> nx.MultiGraph:
        """
        Generates a user interaction graph based on preferences and recipes.

        Each node is a user (yourself or your close neighbors) and each edge
        represents a recipe with the same rating between two users.

        Parameters
        ----------
        type : int
            - `1` : Liked recipes.
            - `-1` : Disliked recipes.

        Returns
        -------
        nx.MultiGraph
            User interaction graph.

        Raises
        ------
        NoNeighborError
            If no neighbors are available to create the graph.
        """
        logger.debug("Getting user network graph")

        near_neighbor = self.get_near_neighbor
        if near_neighbor.empty:
            logger.warning("No neighbor found")
            raise NoNeighborError("No neighbor found")
        recipe_ids = [recipe_id for recipe_id,
                      rate in self.__preferences.items() if rate == type]
        interactions = self.get_interactions
        interactions = self.pivot_table_of_df(
            interactions.loc[
                interactions[USER_COLUMNS[0]].isin(near_neighbor)])
        missing_recipes = set(recipe_ids) - set(interactions.columns)
        for recipe in missing_recipes:
            interactions[recipe] = 0

        graph = nx.MultiGraph()

        user = pd.Series(0, index=interactions.columns)
        user[recipe_ids] = type
        interactions = pd.concat(
            [pd.DataFrame([user], index=[0]), interactions])

        list_user = (interactions.index).to_list()
        graph.add_nodes_from(
            ["user " + str(neighbor) for neighbor in list_user])

        while list_user:
            for user in range(1, len(list_user)):
                interactions_reduced = interactions.loc[
                    [list_user[0], list_user[user]]]
                interactions_filtered = interactions_reduced.loc[
                    :, (interactions_reduced == type).any(axis=0)]
                interactions_filtered = interactions_filtered.loc[
                    :, (interactions_reduced != 0).any(axis=0)]
                dist = self.abs_deviation(
                    interactions_filtered.loc[list_user[0]],
                    interactions_filtered.loc[list_user[user]])
                recipes_with_edge = dist[dist == 0].index.to_list()
                for recipe in recipes_with_edge:
                    graph.add_edge(f"user {list_user[0]}",
                                   f"user {list_user[user]}", key=f"{recipe}")
            list_user = list_user[1:]

        graph = nx.relabel_nodes(graph, {"user 0": "you"}, copy=False)

        connected_nodes = set(graph.neighbors("you"))
        connected_nodes.add("you")
        unconnected_nodes = [
            node for node in graph.nodes if node not in connected_nodes]
        graph.remove_nodes_from(unconnected_nodes)

        return graph

    def get_neighbor_data(self, type):
        """
        Analyzes interactions between the main user and their close neighbors
        to identify commonly liked recipes, commonly disliked recipes, and
        recipes to recommend.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns:
            - "Common_likes": Number of commonly liked recipes.
            - "Common_dislikes": Number of commonly disliked recipes.
            - "Recipes to recommend": Number of recipes to recommend.
        """
        logger.debug("Getting neighbors data")

        liked = [recipe_id for recipe_id,
                 rate in self.get_preferences.items() if rate == LIKE]
        disliked = [recipe_id for recipe_id,
                    rate in self.get_preferences.items() if rate == DISLIKE]
        near_neighbor = self.get_near_neighbor

        interactions = self.get_interactions
        interactions = self.pivot_table_of_df(
            interactions.loc[
                interactions[USER_COLUMNS[0]].isin(near_neighbor)])
        missing_recipes = set(liked+disliked) - set(interactions.columns)
        for recipe in missing_recipes:
            interactions[recipe] = 0

        common_likes = (interactions[liked] == LIKE).sum(axis=1)
        common_dislikes = (interactions[disliked] == DISLIKE).sum(axis=1)

        remaining_recipes = interactions.drop(columns=liked)
        to_recommend = (remaining_recipes == LIKE).sum(axis=1)

        df = pd.DataFrame({
            NEIGHBOR_DATA[0]: common_likes,
            NEIGHBOR_DATA[1]: common_dislikes,
            NEIGHBOR_DATA[2]: to_recommend
        })

        df = df.sort_values(
            by=(NEIGHBOR_DATA[0] if type == LIKE else NEIGHBOR_DATA[1]),
            ascending=False)

        return df
