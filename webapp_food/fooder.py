""" Main file of the web application.
It allows the user to choose between a main dish or a dessert,
to like or dislike the recipes proposed and
to see the explanations of the website.
The user can also see the recommended recipes and their details."""
import streamlit as st
from webapp_food.utils import update_preferences, print_image, \
    ImageError, fetch_recipe_details
from webapp_food.user_fooder import User
import pandas as pd
import logging

# Page state variables
EXPLANATIONS = HISTORY = False


"""
Page management: handling of the different variables
depending on the user's actions on the website
"""
if not st.session_state:
    st.session_state.raw_recipes = pd.read_csv(
        'data/PP_recipes_data.csv', index_col=0)
    st.session_state.logger = logging.getLogger(__name__)
    logging.basicConfig(filename='fooder.log', level=logging.INFO)

if st.session_state.get("like"):
    logging.debug("Like button clicked")
    update_preferences(st.session_state.user,
                       st.session_state.last_recommended_index, 1)

if st.session_state.get("dislike"):
    logging.debug("Dislike button clicked")
    update_preferences(st.session_state.user,
                       st.session_state.last_recommended_index, -1)

if st.session_state.get("main"):
    logging.debug("Main button clicked")
    st.session_state.user = User('main')

if st.session_state.get("dessert"):
    logging.debug("Dessert button clicked")
    st.session_state.user = User('dessert')

if st.session_state.get("explanations"):
    logging.debug("Explanations button clicked")
    EXPLANATIONS = True

if st.session_state.get("retour"):
    logging.debug("Retour button clicked")
    EXPLANATIONS = False
    if st.session_state.get("user"):
        if st.session_state.get("user").get_type_of_dish == 'main':
            MAIN = True
        else:
            DESSERT = True

# Page management: handling of the different pages
MAIN_PAGE = not (EXPLANATIONS) and not (st.session_state.get("user"))
RECOMMENDATION_PAGE = not (EXPLANATIONS) and (
    st.session_state.get("user"))

# Page management: different styles for the website
st.markdown(
    """
    <style>
    .css-18e3th9 {
        padding-top: 0;
    }
    .block-container {
        padding-top: 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    h1 {
        text-align: center;
        color: pink;
        height: 150px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
        <style>
        div.stButton {
            display: flex;
            justify-content: center;
        }
        div.stButton > button {
            padding: 20px 40px;
            font-size: 20px;
            border-radius: 10px;
        }
        </style>
        """,
    unsafe_allow_html=True
)
# Page display: First page of the website
if MAIN_PAGE:
    st.title("Fooder")
    st.write(
        """
        <div style="text-align: center;font-size:20px">
            Are you in the mood for a main dish or a dessert? Choose one below:
            <br><br><br>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
# Management of the sidebar
if RECOMMENDATION_PAGE or MAIN_PAGE:
    st.sidebar.button(
        "Explanations on the website", key="explanations",
        help="Explain website's algorithm and dataset used")
# Management of History
if st.session_state.get("user") and not EXPLANATIONS:
    st.sidebar.write("History of your preferences:")
    for (key, preference_value) in reversed(
            st.session_state.user.get_preferences.items()):
        if st.sidebar.button(st.session_state.raw_recipes.loc[key]['name'] +
                             "  \nRating: "+str(preference_value), key=key):
            st.session_state.last_recommended_index = key
            HISTORY = True
            RECOMMENDATION_PAGE = True
# Page display: Recommendation page
if RECOMMENDATION_PAGE:
    if not HISTORY:
        st.session_state.last_recommended_index = \
            st.session_state.user.recipe_suggestion()
    else:
        st.session_state.user.del_preferences(
            st.session_state.last_recommended_index)
    st.write("""
             <div style="text-align: center; font-size:20px">
             Here is a recipe for you
             (please feel free to expand the recipe's details) <br>
             Let us know if you like it or not so that
             we can recommend a better one next.  <br>
             For that, click on the 'like' and 'dislike' buttons below:
             </div>
             """,
             unsafe_allow_html=True)
    st.title(
        st.session_state.raw_recipes.loc[
            st.session_state.last_recommended_index]['name'])
    col1, col2, col3 = st.columns(
        [1, 1, 1], gap="small", vertical_alignment="center")
    col1.button("❌", key="dislike", help="Dislike", use_container_width=True)
    col3.button("✅", key="like", help="Like", use_container_width=True)
    try:
        images = print_image(
            st.session_state.raw_recipes.loc[
                st.session_state.last_recommended_index]['name'], 1)[0]
        col2.markdown(
            f"""
            <div style="text-align: center;">
                <img src="{images}" style="height: 200px;
                object-fit: cover; border-radius: 50%;
                border: 2px solid #000;">
            </div>
            """,
            unsafe_allow_html=True)
    except ImageError as e:
        col2.write(e)
    st.write("")
    col1, col2 = st.columns(2, gap="small")
    steps, ingredients = fetch_recipe_details(
        st.session_state.raw_recipes, st.session_state.last_recommended_index)
    exp = col1.expander("Recipe's steps")
    exp.write('  \n'.join(steps))
    exp2 = col2.expander("Recipe's ingredients")
    exp2.write('  \n'.join(ingredients))
    st.write(
        """
    <div style="text-align: center;">
        <br><br><br><br>
        Choosing a new type of dish will reset your recommendation algorithm
        <br><br>
    </div>
    """,
        unsafe_allow_html=True,
    )
# Change of type of dish: all pages but explanation page
if not EXPLANATIONS:
    col1, col2 = st.columns(2)
    col1.button("Main Dish", key="main")
    col2.button("Dessert", key="dessert")
# Page display: explanations page
else:
    st.write(
        """
        Fooder est un site de recommandation de recettes de cuisine.
        Vous pouvez aimer ou ne pas aimer les recettes qui vous
        sont proposées pour affiner les recommandations suivantes.
        """
    )
    st.sidebar.button("Retour", key="retour")
