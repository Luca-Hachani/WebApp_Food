"""
Module contenant la classe User pour la recommandation de recettes.
"""
# Importation des librairies
from dataclasses import dataclass, field
from webapp_food.utils import NoNeighborError
import numpy as np
import pandas as pd
import networkx as nx
import logging

logger = logging.getLogger(__name__)


@dataclass
class User:
    """
    Classe représentant un utilisateur et ses interactions avec des recettes,
    notamment pour proposer des suggestions de recettes basées sur
    ses préférences.

    Attributs :
    ----------
    _type_of_dish : str
        Type de plat préféré de l'utilisateur (doit être "main" ou "dessert").
    _preferences : dict
        Dictionnaire contenant les préférences de l'utilisateur,
        où les clés sont les IDs de recettes
        et les valeurs sont les notes attribuées
        (par défaut, dictionnaire vide).
    _interactions_main : pd.DataFrame
        Dataset contenant les interactions utilisateur-recette pour
        les plats principaux (chargé dynamiquement).
    _interactions_dessert : pd.DataFrame
        Dataset contenant les interactions utilisateur-recette pour les
        desserts (chargé dynamiquement).

    Méthodes :
    ---------
    __post_init__() -> None
        Méthode exécutée après l'initialisation pour valider le type de plat et
        charger les datasets.

    validity_type_of_dish(type_of_dish: str) -> None
        Vérifie si le type de plat est valide ("main" ou "dessert"). Lève une
        erreur en cas d'invalidité.

    pivot_table_of_df(interactions_reduce: pd.DataFrame) -> pd.DataFrame
        Transforme un DataFrame d'interactions en une table pivotée avec
        les IDs d'utilisateur
        comme index et les IDs de recettes comme colonnes.

    abs_deviation(recipes_rating: np.ndarray, interactions_pivot: pd.DataFrame)
    -> pd.DataFrame
        Calcule la déviation absolue entre les notes d'une recette et les
        interactions existantes.

    near_neighbor(self, recipes_id: list, interactions: pd.DataFrame,
    interactions_pivot_input: pd.DataFrame) -> pd.DataFrame
        Sélectionne les utilisateurs voisins proches basés sur leurs distances
        et leurs interactions.

    load_datasets() -> None
        Charge les datasets pour les plats principaux et les desserts,
        si ce n'est pas déjà fait.

    get_type_of_dish() -> str
        Retourne le type de plat préféré de l'utilisateur.

    get_preferences() -> dict
        Retourne le dictionnaire des préférences de l'utilisateur.

    get_interactions_main() -> pd.DataFrame
        Retourne le dataset des interactions utilisateur-recette
        pour les plats principaux.

    def get_interactions_dessert() -> pd.DataFrame
        Retourne le dataset des interactions utilisateur-recette
        pour les desserts.

    recipe_suggestion() -> int
        Propose une recette basée sur les préférences de l'utilisateur et
        les interactions existantes.
        Si aucune préférence n'existe, une recette aléatoire est suggérée.

    add_preferences(recipe_suggested: int, rating: int) -> None
        Ajoute une préférence pour une recette donnée avec une note spécifique.

    del_preferences(recipe_deleted: int) -> None
        Supprime une préférence associée à une recette donnée.

    Notes :
    ------
    - Les interactions sont stockées dans des fichiers CSV, chargés
    au moment de l'exécution.
    - La méthode `recipe_suggestion` implémente un système de
    recommandation simple basé sur la similarité
      des utilisateurs avec des distances absolues.

    Exemple d'utilisation :
    -----------------------
    # Créer un utilisateur pour les plats principaux
    user = User(_type_of_dish="main")

    # Ajouter une préférence
    user.add_preferences(recipe_suggested=123, rating= +1 ou-1)

    # Proposer une recette
    suggestion = user.recipe_suggestion()

    # Supprimer une préférence
    user.del_preferences(recipe_deleted=123)
    """

    _type_of_dish: str  # Attribut protégé d'instance
    # Attribut protégé d'instance
    _preferences: dict = field(default_factory=dict)
    _interactions_main: pd.DataFrame = field(
        init=False, repr=False)  # Chargé au runtime
    _interactions_dessert: pd.DataFrame = field(
        init=False, repr=False)  # Chargé au runtime
    _near_neighbor: pd.DataFrame = field(
        init=False, repr=False)  # Chargé au runtime

    # post initialisation
    def __post_init__(self) -> None:
        """
        Exécutée après l'initialisation de la classe.

        Vérifie si le type de plat est valide et charge les datasets
        des interactions
        pour les plats principaux et les desserts.

        Raises:
        ------
        ValueError:
            Si le type de plat (_type_of_dish) est invalide.
        """
        logger.debug(
            "User instance created, \
            checking type of dish and loading datasets")
        # Teste la validité du type de plat
        self.validity_type_of_dish(self._type_of_dish)

        # Charge les datasets (une seule fois,
        # pour éviter une surcharge inutile)
        self.load_datasets()

        # Initialise near neighbors at None
        self._near_neighbor = pd.DataFrame()

    # static methods
    @staticmethod
    def validity_type_of_dish(type_of_dish: str) -> None:
        """
        Vérifie si le type de plat est valide.

        Parameters:
        ----------
        type_of_dish : str
            Type de plat fourni (doit être "main" ou "dessert").

        Raises:
        ------
        ValueError:
            Si le type de plat n'est pas "main" ou "dessert".
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
        Transforme un DataFrame d'interactions utilisateur-recette
        en une table pivotée.

        Parameters:
        ----------
        interactions_reduce : pd.DataFrame
            DataFrame des interactions filtrées, contenant les
            colonnes "user_id", "recipe_id", et "rating".

        Returns:
        -------
        pd.DataFrame:
            Table pivotée avec les IDs des utilisateurs en index,
            les IDs des recettes en colonnes,
            et les évaluations en valeurs. Les valeurs manquantes
            sont remplacées par 0.
        """
        logger.debug("Pivoting DataFrame of interactions")
        interactions_pivot = interactions_reduce.pivot(
            index='user_id', columns='recipe_id', values='rate')
        interactions_pivot = interactions_pivot.fillna(0)
        interactions_pivot.columns.name = None
        interactions_pivot.index.name = None
        return interactions_pivot

    @staticmethod
    def abs_deviation(recipes_rating: np.ndarray, interactions_pivot: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule la déviation absolue entre les préférences du
        nouvel utilisateur pour une recette et les interactions existantes.

        Parameters:
        ----------
        recipes_rating : np.ndarray
            Préférences attribuées à des recettes par le nouvel
            utilisateur (tableau 1D).
        interactions_pivot : pd.DataFrame
            Table pivotée des interactions contenant les notes
            des utilisateurs pour chaque recette.

        Returns:
        -------
        pd.DataFrame:
            DataFrame contenant les déviations absolues entre
            les préférences du nouvel utilisateur
            et celles des autres utilisateurs.
        """
        logger.debug(
            "Calculating absolute deviation between user \
            preferences and existing interactions")
        interactions_abs = np.abs(
            interactions_pivot-recipes_rating)
        return interactions_abs

    @staticmethod
    def near_neighbor(recipes_id: list, interactions: pd.DataFrame,
                      interactions_pivot_input: pd.DataFrame) -> pd.DataFrame:
        """
        Sélectionne les utilisateurs voisins proches basés sur
        la distance et leurs interactions.

        Parameters:
        ----------
        recipes_id : list
            Liste des IDs de recettes déjà révisées par le nouvel utilisateur.
        interactions : pd.DataFrame
            DataFrame contenant les interactions utilisateur-recette.
        interactions_pivot_input : pd.DataFrame
            Table pivotée contenant aussi la colonne distance entre nouvel
            utilisateur et utilisateurs voisins.

        Returns:
        -------
        pd.DataFrame:
            Interactions filtrées des voisins proches pour des recettes
            non révisées par le nouvel utilisateur.
        """
        logger.debug(
            "Selecting near neighbors based on distance and interactions")
        user_prox_id = interactions_pivot_input.sort_values(
            "dist").head(5).index
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
        Charge les datasets d'interactions utilisateur-recette pour
        les plats principaux et les desserts.

        Notes:
        ------
        - Les fichiers CSV sont chargés uniquement une fois
        au niveau de la classe.
        - Les fichiers doivent se trouver aux emplacements spécifiés
        ("data/data/PP_user_main_dishes.csv" et "data/PP_user_desserts").
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
        Retourne le type de plat désiré par l'utilisateur.

        Returns:
        -------
        str:
            Type de plat ("main" ou "dessert").
        """
        logger.debug("Getting type of dish for user")
        return self._type_of_dish

    @property
    def get_preferences(self) -> dict:
        """
        Retourne le dictionnaire des préférences de l'utilisateur.

        Returns:
        -------
        dict:
            Dictionnaire contenant les IDs de recettes comme clés
            et les notes attribuées comme valeurs.
        """
        logger.debug("Getting preferences for user")
        return self._preferences

    @property
    def get_interactions_main(self) -> pd.DataFrame:
        """
        Retourne le dataset des interactions utilisateur-recette
        pour les plats principaux.

        Returns:
        -------
        pd.DataFrame:
            Dataset des interactions pour les plats principaux.
        """
        logger.debug("Getting interactions dataset for main dishes")
        return self._interactions_main

    @property
    def get_interactions_dessert(self) -> pd.DataFrame:
        """
        Retourne le dataset des interactions utilisateur-recette
        pour les desserts.

        Returns:
        -------
        pd.DataFrame:
            Dataset des interactions pour les desserts.
        """
        logger.debug("Getting interactions dataset for desserts")
        return self._interactions_dessert

    @property
    def get_interactions(self) -> pd.DataFrame:
        """
        Retourne the dataset for the current used recipes.

        Returns:
        -------
        pd.DataFrame:
            Dataset of interactions.
        """
        logger.debug("Getting interactions dataset")
        if self.get_type_of_dish == "main":
            interactions = self.get_interactions_main
        elif self.get_type_of_dish == "dessert":
            interactions = self.get_interactions_dessert

        return interactions

    # methods
    def recipe_suggestion(self) -> int:
        """
        Propose une recette en fonction des préférences du nouvel
        utilisateur et des interactions existantes.

        Returns:
        -------
        int:
            ID de la recette suggérée.

        Notes:
        ------
        - Si aucune préférence n'existe pour le nouvel utilisateur,
        une recette aléatoire est suggérée.
        - La suggestion repose sur la similarité des utilisateurs
        voisins proches.
        """
        logger.debug("Proposing a recipe suggestion for user")
        interactions = self.get_interactions
        if len(self._preferences) == 0:
            logger.info('user new historic is empty')
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
            interactions_selection = self.near_neighbor(
                recipes_id, interactions, interactions_pivot)
            self._near_neighbor = interactions_selection.index
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
        Ajoute une nouvelle préférence pour une recette spécifique.

        Parameters:
        ----------
        recipe_suggested : int
            ID de la recette à ajouter aux préférences.
        rating : int
            Note attribuée à la recette.
        """
        logger.debug(f"Adding a new preference for recipe {
                     recipe_suggested} with rating {rating}")
        self._preferences[recipe_suggested] = rating

    def del_preferences(self, recipe_deleted: int) -> None:
        """
        Supprime une préférence associée à une recette donnée.

        Parameters:
        ----------
        recipe_deleted : int
            ID de la recette à supprimer des préférences.

        Raises:
        ------
        KeyError:
            Si l'ID de la recette à supprimer n'existe pas dans
            les préférences de l'utilisateur.
        """
        logger.debug(f"Deleting preference for recipe {recipe_deleted}")
        if recipe_deleted in self._preferences:
            del self._preferences[recipe_deleted]
        else:
            logger.info(f'Recipe ID {recipe_deleted} not in user preferences')
            raise KeyError(
                f'The recipe ID {recipe_deleted}\
                is not in the user preferences.')

    def get_graph(self, type: int) -> nx.MultiGraph:
        """
        Génère un graphe d'interactions utilisateur basé sur les préférences
        et les recettes.

        Chaque nœud est un utilisateur (vous-même ou vos voisins proches)
        et chaque arête représente une recette ayant la même note
        entre deux utilisateurs.

        Parameters
        ----------
        type : int
            - `1` : Recettes aimées.
            - `-1` : Recettes non aimées.

        Returns
        -------
        nx.MultiGraph
            Graphe des interactions utilisateur.

        Raises
        ------
        NoNeighborError
            Si aucun voisin n'est disponible pour créer le graphe.
        """
        logger.debug("Getting user network graph")

        if self._near_neighbor.empty:
            logger.warning("No neighbor found")
            raise NoNeighborError("No neighbor found")

        recipe_ids = [recipe_id for recipe_id,
                      rate in self._preferences.items() if rate == type]
        near_neighbor = self._near_neighbor
        interactions = self.get_interactions
        interactions = self.pivot_table_of_df(
            interactions.loc[interactions['user_id'].isin(near_neighbor)])
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
                interactions_reduced = interactions_reduced.map(
                    lambda x: type if x == type else 0)
                interactions_filtered = interactions_reduced.loc[
                    :, (interactions_reduced != 0).any(axis=0)]
                dist = self.abs_deviation(
                    interactions_filtered.loc[list_user[0]],
                    interactions_filtered.loc[list_user[user]])
                recipes_with_edge = dist[dist == 0].index.to_list()
                for recipe in recipes_with_edge:
                    graph.add_edge(f"user {list_user[0]}",
                                   f"user {list_user[user]}", key=f"{recipe}")

            list_user = list_user[1:]

        isolated_nodes = list(nx.isolates(graph))

        if "user 0" in isolated_nodes:
            graph.clear()
            graph.add_node("user 0")

        else:
            graph.remove_nodes_from(isolated_nodes)

        graph = nx.relabel_nodes(graph, {"user 0": "you"}, copy=False)

        return graph

    def get_neighbor_data(self):
        """
        Analyse les interactions entre l'utilisateur principal et ses voisins
        proches pour identifier les recettes aimées en commun, non aimées en
        commun, et les recettes à recommander.

        Returns
        -------
        pd.DataFrame
            DataFrame avec les colonnes :
            - "common_likes" : Nombre de recettes aimées en commun.
            - "common_dislikes" : Nombre de recettes non aimées en commun.
            - "recipes to recommend" : Nombre de recettes à recommander.
        """
        logger.debug("Getting neighbors data")

        liked = [recipe_id for recipe_id,
                 rate in self._preferences.items() if rate == 1]
        disliked = [recipe_id for recipe_id,
                    rate in self._preferences.items() if rate == -1]
        near_neighbor = self._near_neighbor

        interactions = self.get_interactions
        interactions = self.pivot_table_of_df(
            interactions.loc[interactions['user_id'].isin(near_neighbor)])
        missing_recipes = set(liked+disliked) - set(interactions.columns)
        for recipe in missing_recipes:
            interactions[recipe] = 0

        common_likes = (interactions[liked] == 1).sum(axis=1)
        common_dislikes = (interactions[disliked] == -1).sum(axis=1)

        remaining_recipes = interactions.drop(columns=liked)
        to_recommend = (remaining_recipes == 1).sum(axis=1)

        df = pd.DataFrame({
            "Common likes": common_likes,
            "Common dislikes": common_dislikes,
            "Recipes to recommend": to_recommend
        })

        return df
