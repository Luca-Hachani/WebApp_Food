# dependencies
import numpy as np
import pandas as pd
from dataclasses import dataclass, field

@dataclass
class User:
    """
    Classe représentant un utilisateur et ses interactions avec des recettes, 
    notamment pour proposer des suggestions de recettes basées sur ses préférences.

    Attributs :
    ----------
    _type_of_dish : str
        Type de plat préféré de l'utilisateur (doit être "main" ou "dessert").
    _preferences : dict
        Dictionnaire contenant les préférences de l'utilisateur, où les clés sont les IDs de recettes 
        et les valeurs sont les notes attribuées (par défaut, dictionnaire vide).
    _interactions_main : pd.DataFrame
        Dataset contenant les interactions utilisateur-recette pour les plats principaux (chargé dynamiquement).
    _interactions_dessert : pd.DataFrame
        Dataset contenant les interactions utilisateur-recette pour les desserts (chargé dynamiquement).

    Méthodes :
    ---------
    __post_init__() -> None
        Méthode exécutée après l'initialisation pour valider le type de plat et charger les datasets.

    validity_type_of_dish(type_of_dish: str) -> None
        Vérifie si le type de plat est valide ("main" ou "dessert"). Lève une erreur en cas d'invalidité.

    pivot_table_of_df(interactions_reduce: pd.DataFrame) -> pd.DataFrame
        Transforme un DataFrame d'interactions en une table pivotée avec les IDs d'utilisateur 
        comme index et les IDs de recettes comme colonnes.

    abs_deviation(recipes_rating: np.ndarray, interactions_pivot: pd.DataFrame) -> pd.DataFrame
        Calcule la déviation absolue entre les notes d'une recette et les interactions existantes.

    near_neighboor(self, recipes_id: list, interactions: pd.DataFrame, interactions_pivot_input: pd.DataFrame) -> pd.DataFrame
        Sélectionne les utilisateurs voisins proches basés sur leurs distances et leurs interactions.

    load_datasets() -> None
        Charge les datasets pour les plats principaux et les desserts, si ce n'est pas déjà fait.

    dataset_interaction(type_of_dish: str) -> None
        Affiche les informations du dataset correspondant au type de plat ("main" ou "dessert").

    get_type_of_dish() -> str
        Retourne le type de plat préféré de l'utilisateur.

    get_preferences() -> dict
        Retourne le dictionnaire des préférences de l'utilisateur.

    recipe_suggestion() -> int
        Propose une recette basée sur les préférences de l'utilisateur et les interactions existantes.
        Si aucune préférence n'existe, une recette aléatoire est suggérée.

    add_preferences(recipe_suggested: int, rating: float) -> None
        Ajoute une préférence pour une recette donnée avec une note spécifique.

    del_preferences(recipe_deleted: int) -> None
        Supprime une préférence associée à une recette donnée.

    Notes :
    ------
    - Les interactions sont stockées dans des fichiers CSV, chargés au moment de l'exécution.
    - La méthode `recipe_suggestion` implémente un système de recommandation simple basé sur la similarité
      des utilisateurs avec des distances absolues.

    Exemple d'utilisation :
    -----------------------
    # Créer un utilisateur pour les plats principaux
    user = User(_type_of_dish="main")

    # Ajouter une préférence
    user.add_preferences(recipe_suggested=123, rating=4.5)

    # Proposer une recette
    suggestion = user.recipe_suggestion()

    # Supprimer une préférence
    user.del_preferences(recipe_deleted=123)
    """

    _type_of_dish: str  # Attribut protégé d'instance
    _preferences: dict = field(default_factory=dict) # Attribut protégé d'instance
    _interactions_main: pd.DataFrame = field(init=False, repr=False)  # Chargé au runtime
    _interactions_dessert: pd.DataFrame = field(init=False, repr=False)  # Chargé au runtime
    
    # post initialisation
    def __post_init__(self)-> None:
        """
        Exécutée après l'initialisation de la classe.

        Vérifie si le type de plat est valide et charge les datasets des interactions
        pour les plats principaux et les desserts.

        Raises:
        ------
        ValueError:
            Si le type de plat (_type_of_dish) est invalide.
        """
        # Teste la validité du type de plat
        self.validity_type_of_dish(self._type_of_dish)
        
        # Charge les datasets (une seule fois, pour éviter une surcharge inutile)
        self.load_datasets()
    
    # static methods
    @staticmethod
    def validity_type_of_dish(type_of_dish)-> None:
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
        if type_of_dish not in ["main", "dessert"]:
            raise ValueError(f'The type of dish must be "main" or "dessert" only, and not "{type_of_dish}".')
    
    @staticmethod
    def pivot_table_of_df(interactions_reduce) -> pd.DataFrame:
        """
        Transforme un DataFrame d'interactions utilisateur-recette en une table pivotée.

        Parameters:
        ----------
        interactions_reduce : pd.DataFrame
            DataFrame des interactions filtrées, contenant les colonnes "user_id", "recipe_id", et "rating".

        Returns:
        -------
        pd.DataFrame:
            Table pivotée avec les IDs des utilisateurs en index, les IDs des recettes en colonnes,
            et les évaluations en valeurs. Les valeurs manquantes sont remplacées par 0.
        """
        interactions_pivot = interactions_reduce.pivot(index='user_id', columns='recipe_id', values='rating')
        interactions_pivot = interactions_pivot.fillna(0)
        interactions_pivot.columns.name = None
        interactions_pivot.index.name = None
        return interactions_pivot
    
    @staticmethod
    def abs_deviation(recipes_rating, interactions_pivot) -> pd.DataFrame:
        """
        Calcule la déviation absolue entre les préférences du nouvel utilisateur pour une recette et les interactions existantes.

        Parameters:
        ----------
        recipes_rating : np.ndarray
            Préférences attribuées à des recettes par le nouvel utilisateur (tableau 1D).
        interactions_pivot : pd.DataFrame
            Table pivotée des interactions contenant les notes des utilisateurs pour chaque recette.

        Returns:
        -------
        pd.DataFrame:
            DataFrame contenant les déviations absolues entre les préférences du nouvel utilisateur
            et celles des autres utilisateurs.
        """
        norm_order = 1
        interactions_abs = np.abs(interactions_pivot-recipes_rating)**norm_order
        return interactions_abs
    
    @staticmethod
    def near_neighboor(self, recipes_id, interactions, interactions_pivot_input) -> pd.DataFrame:
        """
        Sélectionne les utilisateurs voisins proches basés sur la distance et leurs interactions.

        Parameters:
        ----------
        recipes_id : list
            Liste des IDs de recettes déjà révisées par le nouvel utilisateur.
        interactions : pd.DataFrame
            DataFrame contenant les interactions utilisateur-recette.
        interactions_pivot_input : pd.DataFrame
            Table pivotée contenant aussi la colonne distance entre nouvel utilisateur et utilisateurs voisins.

        Returns:
        -------
        pd.DataFrame:
            Interactions filtrées des voisins proches pour des recettes non révisées
            par le nouvel utilisateur.
        """
        user_prox_id = interactions_pivot_input.sort_values("dist").head(3).index
        interactions_prox = interactions[interactions['user_id'].isin(user_prox_id)]
        interactions_prox = interactions_prox[~interactions_prox['recipe_id'].isin(recipes_id)]
        interactions_pivot_output = self.pivot_table_of_df(interactions_prox)
        user_prox_id = np.unique(interactions_prox["user_id"])
        interactions_selection = interactions_pivot_output.loc[user_prox_id]
        return interactions_selection
    
    # class methods
    @classmethod
    def load_datasets(cls) -> None:
        """
        Charge les datasets d'interactions utilisateur-recette pour les plats principaux et les desserts.

        Notes:
        ------
        - Les fichiers CSV sont chargés uniquement une fois au niveau de la classe.
        - Les fichiers doivent se trouver aux emplacements spécifiés ("data/Preprocessed_interactions_main.csv" 
        et "data/Preprocessed_interactions_dessert.csv").
        """
        if not hasattr(cls, "_interactions_main") or not hasattr(cls, "_interactions_dessert"):
            cls._interactions_main = pd.read_csv("data/Preprocessed_interactions_main.csv", sep=',')
            cls._interactions_dessert = pd.read_csv("data/Preprocessed_interactions_dessert.csv", sep=',')

    @classmethod
    def dataset_interaction(cls, type_of_dish) -> None:
        """
        Affiche les informations et les premières lignes du dataset correspondant au type de plat.

        Parameters:
        ----------
        type_of_dish : str
            Type de plat ("main" ou "dessert").

        Raises:
        ------
        ValueError:
            Si le type de plat est invalide.
        """
        cls.validity_type_of_dish(type_of_dish)  # Vérifie si le type est valide
        if type_of_dish == "main":
            print(cls._interactions_main.info())
            print(cls._interactions_main.head())
        elif type_of_dish == "dessert":
            print(cls._interactions_dessert.info())
            print(cls._interactions_dessert.head())
    
    # property method
    @property
    def get_type_of_dish(self) -> str:
        """
        Retourne le type de plat désiré par l'utilisateur.

        Returns:
        -------
        str:
            Type de plat ("main" ou "dessert").
        """
        return self._type_of_dish
    
    @property
    def get_preferences(self) -> dict:
        """
        Retourne le dictionnaire des préférences de l'utilisateur.

        Returns:
        -------
        dict:
            Dictionnaire contenant les IDs de recettes comme clés et les notes attribuées comme valeurs.
        """
        return self._preferences
    
    # methods
    def recipe_suggestion(self) -> int:
        """
        Propose une recette en fonction des préférences du nouvel utilisateur et des interactions existantes.

        Returns:
        -------
        int:
            ID de la recette suggérée.

        Notes:
        ------
        - Si aucune préférence n'existe pour le nouvel utilisateur, une recette aléatoire est suggérée.
        - La suggestion repose sur la similarité des utilisateurs voisins proches.
        """
        if self._type_of_dish=="main":
            interactions = self.__class__._interactions_main
        elif self._type_of_dish=="dessert":
            interactions = self.__class__._interactions_dessert
        if len(self._preferences)==0:
            print('user new historic is empty')
            recipe_suggested = interactions["recipe_id"].sample(n=1).iloc[0]
        else :
            recipes_id = list(self._preferences.keys())
            recipes_rating = np.array(list(self._preferences.values())).reshape(1, -1)
            interactions_reduce = interactions[interactions['recipe_id'].isin(recipes_id)]
            interactions_pivot = self.pivot_table_of_df(interactions_reduce)
            interactions_abs = self.abs_deviation(recipes_rating, interactions_pivot)
            interactions_pivot["dist"] = interactions_abs.sum(axis=1)
            interactions_selection = self.near_neighboor(self, recipes_id, interactions, interactions_pivot)
            recipe_suggested = int(interactions_selection.sum(axis=0).idxmax())
        return recipe_suggested
    
    def add_preferences(self, recipe_suggested, rating) -> None:
        """
        Ajoute une nouvelle préférence pour une recette spécifique.

        Parameters:
        ----------
        recipe_suggested : int
            ID de la recette à ajouter aux préférences.
        rating : int
            Note attribuée à la recette.
        """
        self._preferences[recipe_suggested] = rating
    
    def del_preferences(self, recipe_deleted) -> None:
        """
        Supprime une préférence associée à une recette donnée.

        Parameters:
        ----------
        recipe_deleted : int
            ID de la recette à supprimer des préférences.
        """
        del self._preferences[recipe_deleted]