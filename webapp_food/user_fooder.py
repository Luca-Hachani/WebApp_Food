# dependencies
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class User:
    type_of_dish_: str  # Attribut d'instance
    recipes_preferences: dict = field(default_factory=dict) # Attribut d'instance
    interactions_main_: pd.DataFrame = field(init=False, repr=False)  # Chargé au runtime
    interactions_dessert_: pd.DataFrame = field(init=False, repr=False)  # Chargé au runtime
    
    # post initialisation
    def __post_init__(self):
        # Teste la validité du type de plat
        self.test_type_of_dish(self.type_of_dish_)
        
        # Charge les datasets (une seule fois, pour éviter une surcharge inutile)
        self.load_datasets()
    
    # static methods
    @staticmethod
    def test_type_of_dish(type_of_dish):
        """Vérifie si le type de plat est valide."""
        if type_of_dish not in ["main", "dessert"]:
            raise ValueError(f'The type of dish must be "main" or "dessert" only, and not "{type_of_dish}".')
    
    @staticmethod
    def pivot_table_of_df(interactions_reduce):
        interactions_pivot = interactions_reduce.pivot(index='user_id', columns='recipe_id', values='rating')
        interactions_pivot = interactions_pivot.fillna(0)
        interactions_pivot.columns.name = None
        interactions_pivot.index.name = None
        return interactions_pivot
    
    @staticmethod
    def abs_deviation(recipes_rating, interactions_pivot):
        norm_order = 1
        interactions_abs = np.abs(interactions_pivot-recipes_rating)**norm_order
        return interactions_abs
    
    @staticmethod
    def near_neighboor(self, recipes_id, interactions, interactions_pivot_input):
        user_prox_id = interactions_pivot_input.sort_values("dist").head(3).index
        interactions_prox = interactions[interactions['user_id'].isin(user_prox_id)]
        interactions_prox = interactions_prox[~interactions_prox['recipe_id'].isin(recipes_id)]
        interactions_pivot_output = self.pivot_table_of_df(interactions_prox)
        user_prox_id = np.unique(interactions_prox["user_id"])
        interactions_selection = interactions_pivot_output.loc[user_prox_id]
        return interactions_selection
    
    # class methods
    @classmethod
    def load_datasets(cls):
        """Charge les datasets une seule fois pour tous les objets User."""
        if not hasattr(cls, "interactions_main_") or not hasattr(cls, "interactions_dessert_"):
            cls.interactions_main_ = pd.read_csv("data/Preprocessed_interactions_main.csv", sep=',')
            cls.interactions_dessert_ = pd.read_csv("data/Preprocessed_interactions_dessert.csv", sep=',')

    @classmethod
    def dataset_interaction(cls, type_of_dish):
        """Affiche les informations du dataset en fonction du type de plat."""
        cls.test_type_of_dish(type_of_dish)  # Vérifie si le type est valide
        if type_of_dish == "main":
            print(cls.interactions_main_.info())
            print(cls.interactions_main_.head())
        elif type_of_dish == "dessert":
            print(cls.interactions_dessert_.info())
            print(cls.interactions_dessert_.head())
    
    # property method
    @property
    def get_type_of_dish(self):
        return self.type_of_dish_
    
    @property
    def get_recipes_preferences(self):
        return self.recipes_preferences
    
    # methods
    def recipe_suggestion(self):
        if self.type_of_dish_=="main":
            interactions = self.__class__.interactions_main_
        elif self.type_of_dish_=="dessert":
            interactions = self.__class__.interactions_dessert_
        if len(self.recipes_preferences)==0:
            print('user new historic is empty')
            recipe_suggested = interactions["recipe_id"].sample(n=1).iloc[0]
        else :
            recipes_id = list(self.recipes_preferences.keys())
            recipes_rating = np.array(list(self.recipes_preferences.values())).reshape(1, -1)
            interactions_reduce = interactions[interactions['recipe_id'].isin(recipes_id)]
            interactions_pivot = self.pivot_table_of_df(interactions_reduce)
            interactions_abs = self.abs_deviation(recipes_rating, interactions_pivot)
            interactions_pivot["dist"] = interactions_abs.sum(axis=1)
            interactions_selection = self.near_neighboor(self, recipes_id, interactions, interactions_pivot)
            recipe_suggested = int(interactions_selection.sum(axis=0).idxmax())
        return recipe_suggested
    
    def add_preferences(self, recipe_suggested, rating):
        self.recipes_preferences[recipe_suggested] = rating
    
    def del_preferences(self, recipe_deleted):
        del self.recipes_preferences[recipe_deleted]
    
#test

# Créer un utilisateur
type_of_dish = "main"
dico = {116345 : 1, 32907 : -1}
# dico : Dict[str, float] = {}
user1 = User(type_of_dish_=type_of_dish, recipes_preferences=dico)
print("recipe historic =", list(dico.keys()))
print("rating historic =", list(dico.values()))
print("type of dish =", user1.get_type_of_dish)
print("former dict of user's preferences =", user1.get_recipes_preferences)

# Lui Suggérer une recette
recipe_suggested = user1.recipe_suggestion()
print("recipes suggested =", recipe_suggested)

# Ajouter ses préférences
rating = 1
user1.add_preferences(recipe_suggested=recipe_suggested, rating=rating)
print("new dict of user's preferences =", user1.get_recipes_preferences)

# Supprimer ses préférences
user1.del_preferences(recipe_deleted=116345)
print("edited dict of user's preferences =", user1.get_recipes_preferences)

# Affiche le dataset
# User.dataset_interaction(type_of_dish)