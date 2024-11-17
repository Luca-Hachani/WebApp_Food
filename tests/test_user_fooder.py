import pytest
import pandas as pd
import numpy as np
from webapp_food import user_fooder as uf

# #test

# # Créer un utilisateur
# type_of_dish = "main"
# dico = {116345 : 1, 32907 : -1}
# # dico : {}
# user1 = uf.User(_type_of_dish=type_of_dish, _preferences=dico)
# print("recipe historic =", list(dico.keys()))
# print("rating historic =", list(dico.values()))
# print("type of dish =", user1.get_type_of_dish)
# print("former dict of user's preferences =", user1.get_preferences)

# # Lui Suggérer une recette
# recipe_suggested = user1.recipe_suggestion()
# print("recipes suggested =", recipe_suggested)

# # Ajouter ses préférences
# rating = 1
# user1.add_preferences(recipe_suggested=recipe_suggested, rating=rating)
# print("new dict of user's preferences =", user1.get_preferences)

# # Supprimer ses préférences
# user1.del_preferences(recipe_deleted=116345)
# print("edited dict of user's preferences =", user1.get_preferences)

# # Affiche le dataset
# # User.dataset_interaction(type_of_dish)

# Configuration des données pour les tests
@pytest.fixture
def setup_user():
    # Simulation des datasets
    main_data = pd.DataFrame({
        'user_id': [1, 2, 3],
        'recipe_id': [101, 102, 103],
        'rating': [1, 1, -1]
    })
    dessert_data = pd.DataFrame({
        'user_id': [1, 2],
        'recipe_id': [201, 202],
        'rating': [1, -1]
    })

    # Simuler les fichiers CSV dans la classe User
    uf.User._interactions_main = main_data
    uf.User._interactions_dessert = dessert_data

    # Créer une instance utilisateur
    user = uf.User(_type_of_dish="main")
    return user

# Test `validity_type_of_dish`
def test_validity_type_of_dish_valid():
    uf.User.validity_type_of_dish("main")
    uf.User.validity_type_of_dish("dessert")

def test_validity_type_of_dish_invalid():
    with pytest.raises(ValueError):
        uf.User.validity_type_of_dish("invalid")

# Test `pivot_table_of_df`
def test_pivot_table_of_df():
    main_data = pd.DataFrame({
        'user_id': [1, 2, 3],
        'recipe_id': [101, 102, 103],
        'rating': [1, 1, -1]
    })
    pivot_table = uf.User.pivot_table_of_df(main_data)
    assert pivot_table.shape == (3, 3)
    assert list(pivot_table.columns) == [101, 102, 103]

# Test `abs_deviation`
def test_abs_deviation():
    recipes_rating = np.array([[4.0, 5.0, 3.0]])
    pivot_table = pd.DataFrame({
        101: [ 1, 0, 0],
        102: [ 0, 1, 0],
        103: [ 0, 0,-1]
    })
    abs_dev = uf.User.abs_deviation(recipes_rating, pivot_table)
    assert abs_dev.shape == pivot_table.shape

# Test `add_preferences` et `del_preferences`
def test_add_preferences(setup_user):
    user = setup_user
    user.add_preferences(101, 1)
    assert 101 in user.get_preferences
    assert user.get_preferences[101] == 1

def test_del_preferences(setup_user):
    user = setup_user
    user.add_preferences(101, 1)
    user.del_preferences(101)
    assert 101 not in user.get_preferences
