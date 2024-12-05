import pytest
import pandas as pd
import numpy as np
from webapp_food import user_fooder as uf

# #test

# # Create a user
# type_of_dish = "main"
# dico = {116345 : 1, 32907 : -1}
# # dico : {}
# user1 = uf.User(_type_of_dish=type_of_dish, _preferences=dico)
# print("recipe historic =", list(dico.keys()))
# print("rating historic =", list(dico.values()))
# print("type of dish =", user1.get_type_of_dish)
# print("former dict of user's preferences =", user1.get_preferences)

# # Suggest a recipe
# recipe_suggested = user1.recipe_suggestion()
# print("recipes suggested =", recipe_suggested)

# # Add preferences
# rating = 1
# user1.add_preferences(recipe_suggested=recipe_suggested, rating=rating)
# print("new dict of user's preferences =", user1.get_preferences)

# # Delete preferences
# user1.del_preferences(recipe_deleted=116345)
# print("edited dict of user's preferences =", user1.get_preferences)

# # Display the dataset
# # User.dataset_interaction(type_of_dish)

# Data configuration for tests


@pytest.fixture
def setup_user():
    # Dataset simulation
    main_data = pd.DataFrame({
        'user_id': [1, 2, 3, 4, 4],
        'recipe_id': [101, 102, 103, 102, 103],
        'rate': [1, 1, -1, 1, 1]
    })
    dessert_data = pd.DataFrame({
        'user_id': [1, 2],
        'recipe_id': [201, 202],
        'rate': [1, -1]
    })

    # User CSV simulation
    uf.User._interactions_main = main_data
    uf.User._interactions_dessert = dessert_data

    # User creation
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
        'rate': [1, 1, -1]
    })
    pivot_table = uf.User.pivot_table_of_df(main_data)
    assert pivot_table.shape == (3, 3)
    assert list(pivot_table.columns) == [101, 102, 103]

# Test `abs_deviation`


def test_abs_deviation():
    recipes_rating = np.array([[4.0, 5.0, 3.0]])
    pivot_table = pd.DataFrame({
        101: [1, 0, 0],
        102: [0, 1, 0],
        103: [0, 0, -1]
    })
    abs_dev = uf.User.abs_deviation(recipes_rating, pivot_table)
    assert abs_dev.shape == pivot_table.shape

# Test `add_preferences` and `del_preferences`


def test_add_preferences(setup_user):
    user = setup_user
    user.add_preferences(101, 1)
    assert 101 in user.get_preferences
    assert user.get_preferences[101] == 1

# Test that a deleted recipe is no longer in user preferences


def test_del_preferences(setup_user):
    user = setup_user
    user.add_preferences(101, 1)
    user.del_preferences(101)
    assert 101 not in user.get_preferences

# Test that deleting a missing recipe in user preferences raises a KeyError


def test_del_preferences_invalid(setup_user):
    user = setup_user
    with pytest.raises(KeyError):
        user.del_preferences(999)

# Test recipe suggestion


def test_recipe_suggestion(setup_user):
    # Test if the user as no preferences
    user = setup_user
    recipe_suggested = user.recipe_suggestion()
    assert recipe_suggested in user.get_interactions_main['recipe_id'].values
    assert recipe_suggested not in user.get_preferences.keys()
    # Test if the user has no near neighbors
    user.add_preferences(101, 1)
    recipe_suggested = user.recipe_suggestion()
    assert recipe_suggested not in user.get_preferences.keys()
    assert recipe_suggested in user.get_interactions_main['recipe_id'].values
    # Test if all recipes have been suggested
    user.add_preferences(102, -1)
    recipe_suggested = user.recipe_suggestion()
    user.add_preferences(103, 1)
    with pytest.raises(ValueError):
        recipe_suggested = user.recipe_suggestion()


# Test `get_graph`


def test_get_graph_no_neighbors(setup_user):
    user = setup_user

    with pytest.raises(uf.NoNeighborError, match="No neighbor found"):
        user.get_graph(1)

    user.add_preferences(101, 1)
    user.recipe_suggestion()

    with pytest.raises(uf.NoNeighborError, match="No neighbor found"):
        user.get_graph(1)


def test_get_graph(setup_user):
    user = setup_user
    user.add_preferences(102, 1)
    user.recipe_suggestion()

    graph = user.get_graph(1)
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert ("you", "user: 4") in graph.edges or (
        "user: 4", "you") in graph.edges

    graph = user.get_graph(-1)
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 0


# Test `get_neighbor_data`


def test_common_likes(setup_user):
    user = setup_user

    user.add_preferences(102, 1)
    user.recipe_suggestion()

    df = user.get_neighbor_data()

    assert df.loc[4, "common likes"] == 1
    assert df.loc[4, "common dislikes"] == 0
    assert df.loc[4, "recipes to recommend"] == 1
