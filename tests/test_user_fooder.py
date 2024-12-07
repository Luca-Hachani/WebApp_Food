import pytest
import pandas as pd
import numpy as np
from webapp_food import user_fooder as uf
from webapp_food.settings import LIKE, DISLIKE, USER_COLUMNS, \
    NEIGHBOR_DATA

# Data configuration for tests


@pytest.fixture
def setup_user():
    # Dataset simulation
    main_data = pd.DataFrame({
        USER_COLUMNS[0]: [1, 2, 3, 4, 4],
        USER_COLUMNS[1]: [101, 102, 103, 102, 103],
        USER_COLUMNS[2]: [LIKE, LIKE, DISLIKE, LIKE, LIKE]
    })
    dessert_data = pd.DataFrame({
        USER_COLUMNS[0]: [1, 2],
        USER_COLUMNS[1]: [201, 202],
        USER_COLUMNS[2]: [LIKE, DISLIKE]
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
        USER_COLUMNS[0]: [1, 2, 3],
        USER_COLUMNS[1]: [101, 102, 103],
        USER_COLUMNS[2]: [LIKE, LIKE, DISLIKE]
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
    user.add_preferences(101, LIKE)
    assert 101 in user.get_preferences
    assert user.get_preferences[101] == LIKE

# Test that a deleted recipe is no longer in user preferences


def test_del_preferences(setup_user):
    user = setup_user
    user.add_preferences(101, LIKE)
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
    assert recipe_suggested in user.get_interactions_main[
        USER_COLUMNS[1]].values
    assert recipe_suggested not in user.get_preferences.keys()
    # Test if the user has no near neighbors
    user.add_preferences(101, LIKE)
    recipe_suggested = user.recipe_suggestion()
    assert recipe_suggested not in user.get_preferences.keys()
    assert recipe_suggested in user.get_interactions_main[
        USER_COLUMNS[1]].values
    # Test if all recipes have been suggested
    user.add_preferences(102, DISLIKE)
    recipe_suggested = user.recipe_suggestion()
    user.add_preferences(103, LIKE)
    with pytest.raises(ValueError):
        recipe_suggested = user.recipe_suggestion()


# Test `get_graph`


def test_get_graph_no_neighbors(setup_user):
    user = setup_user

    with pytest.raises(uf.NoNeighborError, match="No neighbor found"):
        user.get_graph(LIKE)

    user.add_preferences(101, LIKE)
    user.recipe_suggestion()

    with pytest.raises(uf.NoNeighborError, match="No neighbor found"):
        user.get_graph(LIKE)


def test_get_graph(setup_user):
    user = setup_user
    user.add_preferences(102, LIKE)
    user.recipe_suggestion()

    graph = user.get_graph(LIKE)

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert ("you", "user 4", "102") in graph.edges or (
        "user 4", "you", "102") in graph.edges

    graph = user.get_graph(DISLIKE)
    assert len(graph.nodes) == 1
    assert len(graph.edges) == 0


# Test `get_neighbor_data`

def test_common_likes(setup_user,):
    user = setup_user

    user.add_preferences(102, LIKE)
    user.recipe_suggestion()

    df = user.get_neighbor_data(LIKE)

    assert df.loc[4, NEIGHBOR_DATA[0]] == 1
    assert df.loc[4, NEIGHBOR_DATA[1]] == 0
    assert df.loc[4, NEIGHBOR_DATA[2]] == 1
