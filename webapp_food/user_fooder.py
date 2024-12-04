"""
Module containing the User class for recipe recommendations.
"""
# Importation des librairies
from dataclasses import dataclass, field
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class User:
    """
    Class representing a user and their interactions with recipes,
    particularly for suggesting recipes based on their preferences.

    Attributes
    ----------
    _type_of_dish : str
        The preferred type of dish for the user (must be "main" or "dessert").

    _preferences : dict
        A dictionary containing the user's preferences,
        where the keys are recipe IDs and the values are the ratings given
        (default: empty dictionary).

    _interactions_main : pd.DataFrame
        Dataset containing user-recipe interactions for main dishes
        (dynamically loaded).

    _interactions_dessert : pd.DataFrame
        Dataset containing user-recipe interactions for desserts
        (dynamically loaded).

    Methods
    -------
    __post_init__() -> None
        Method executed after initialization to validate the dish type
        and load datasets.

    validity_type_of_dish(type_of_dish: str) -> None
        Checks if the dish type is valid ("main" or "dessert").
        Raises an error if invalid.

    pivot_table_of_df(interactions_reduce: pd.DataFrame) -> pd.DataFrame
        Converts a DataFrame of interactions into a pivot table with user IDs
        as rows and recipe IDs as columns.

    abs_deviation(recipes_rating: np.ndarray, interactions_pivot: pd.DataFrame)
    -> pd.DataFrame
        Calculates the absolute deviation between recipe ratings and
        existing interactions.

    near_neighboor(recipes_id: list, interactions: pd.DataFrame,
    interactions_pivot_input: pd.DataFrame) -> pd.DataFrame
        Selects close neighbor users based on their distances and interactions.

    load_datasets() -> None
        Loads datasets for main dishes and desserts, if not already loaded.

    get_type_of_dish() -> str
        Returns the user's preferred type of dish.

    get_preferences() -> dict
        Returns the user's preferences dictionary.

    get_interactions_main() -> pd.DataFrame
        Returns the dataset of user-recipe interactions for main dishes.

    get_interactions_dessert() -> pd.DataFrame
        Returns the dataset of user-recipe interactions for desserts.

    recipe_suggestion() -> int
        Suggests a recipe based on the user's preferences and existing
        interactions. If no preferences exist, a random recipe is suggested.

    add_preferences(recipe_suggested: int, rating: int) -> None
        Adds a preference for a specific recipe with a given rating.

    del_preferences(recipe_deleted: int) -> None
        Removes a preference associated with a specific recipe.

    Notes
    -----
    - Interactions are stored in CSV files, loaded at runtime.
    - The `recipe_suggestion` method implements a simple recommendation system
      based on user similarity using absolute distances.

    Example
    -------
    #1 Create a user for main dishes :
    user = User(_type_of_dish="main")

    #2 Suggest a recipe :
    suggestion = user.recipe_suggestion()

    #3 Add a preference :
    user.add_preferences(recipe_suggested=123, rating=+1/-1)

    #* Remove a preference :
    user.del_preferences(recipe_deleted=123)
    """

    _type_of_dish: str  # Attribut protégé d'instance
    # Attribut protégé d'instance
    _preferences: dict = field(default_factory=dict)
    _interactions_main: pd.DataFrame = field(
        init=False, repr=False)  # Chargé au runtime
    _interactions_dessert: pd.DataFrame = field(
        init=False, repr=False)  # Chargé au runtime

    # post initialisation
    def __post_init__(self) -> None:
        """
        Executed after the class initialization.

        Validates the dish type and loads interaction datasets for
        main dishes and desserts.

        Raises
        ------
        ValueError
            If the dish type (_type_of_dish) is invalid.
        """
        logger.debug(
            "User instance created, \
            checking type of dish and loading datasets")
        # Test dish type validity
        self.validity_type_of_dish(self._type_of_dish)
        # Load the datasets only once to avoid unnecessary overhead.
        self.load_datasets()

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
        if type_of_dish not in ["main", "dessert"]:
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
            index='user_id', columns='recipe_id', values='rate')
        interactions_pivot = interactions_pivot.fillna(0)
        interactions_pivot.columns.name = None
        interactions_pivot.index.name = None
        return interactions_pivot

    @staticmethod
    def abs_deviation(recipes_rating: np.ndarray,
                      interactions_pivot: pd.DataFrame) -> pd.DataFrame:
        """
        Computes the absolute deviation between a new user's recipe preferences
        and existing interactions.

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
        norm_order = 1
        interactions_abs = np.abs(
            interactions_pivot-recipes_rating)**norm_order
        return interactions_abs

    @staticmethod
    def near_neighboor(recipes_id: list, interactions: pd.DataFrame,
                       interactions_pivot_input: pd.DataFrame) -> pd.DataFrame:
        """
        Selects nearby users based on distances and their interactions.

        Parameters
        ----------
        recipes_id : list
            List of recipe IDs already reviewed by the new user.
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
        user_prox_id = interactions_pivot_input.sort_values(
            "dist").head(3).index
        interactions_prox = interactions[interactions['user_id'].isin(
            user_prox_id)]
        interactions_prox = interactions_prox[~interactions_prox['recipe_id']
                                              .isin(recipes_id)]
        interactions_pivot_output = User.pivot_table_of_df(interactions_prox)
        user_prox_id = np.unique(interactions_prox["user_id"])
        interactions_selection = interactions_pivot_output.loc[user_prox_id]
        return interactions_selection

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
        if not hasattr(cls, "_interactions_main") or \
                not hasattr(cls, "_interactions_dessert"):
            cls._interactions_main = pd.read_csv(
                "data/PP_user_main_dishes.csv", sep=',')
            cls._interactions_dessert = pd.read_csv(
                "data/PP_user_desserts.csv", sep=',')

    # property methods
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
        return self._type_of_dish

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
        return self._preferences

    @property
    def get_interactions_main(self) -> pd.DataFrame:
        """
        Returns the dataset of user-recipe interactions for main dishes.

        Returns
        -------
        pd.DataFrame
            The dataset of interactions for main dishes.
        """
        logger.debug("Getting interactions dataset for main dishes")
        return self._interactions_main

    @property
    def get_interactions_dessert(self) -> pd.DataFrame:
        """
        Returns the dataset of user-recipe interactions for desserts.

        Returns
        -------
        pd.DataFrame
            The dataset of interactions for desserts.
        """
        logger.debug("Getting interactions dataset for desserts")
        return self._interactions_dessert

    # methods
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
        interactions = None
        if self._type_of_dish == "main":
            interactions = self.get_interactions_main
        elif self._type_of_dish == "dessert":
            interactions = self.get_interactions_dessert
        if len(self._preferences) == 0:
            logger.info("new user's historic is empty")
            recipe_suggested = interactions["recipe_id"].sample(n=1).iloc[0]
        else:
            recipes_id = list(self._preferences.keys())
            recipes_rating = np.array(
                list(self._preferences.values())).reshape(1, -1)
            interactions_reduce = interactions[interactions['recipe_id'].isin(
                recipes_id)]
            interactions_pivot = self.pivot_table_of_df(interactions_reduce)
            interactions_abs = self.abs_deviation(
                recipes_rating, interactions_pivot)
            interactions_pivot["dist"] = interactions_abs.sum(axis=1)
            interactions_selection = self.near_neighboor(
                recipes_id, interactions, interactions_pivot)
            if interactions_selection.empty:
                # drop recipes already in preferences
                interactions_selection = interactions[
                    ~interactions['recipe_id'].isin(recipes_id)]
                if interactions_selection.empty:
                    logger.info('No more recipes to suggest from the dataset')
                    raise ValueError('No more recipes to suggest.')
                else:
                    logger.info(
                        'No more recipes to suggest from the user preferences,\
                        suggesting a random recipe')
                    recipe_suggested = \
                        interactions_selection["recipe_id"].sample(n=1).iloc[0]
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
        self._preferences[recipe_suggested] = rating

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
        if recipe_deleted in self._preferences:
            del self._preferences[recipe_deleted]
        else:
            logger.info(f'Recipe ID {recipe_deleted} not in user preferences')
            raise KeyError(
                f'The recipe ID {recipe_deleted}\
                is not in the user preferences.')
