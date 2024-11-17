""" Main file of the web application.
It allows the user to choose between a main dish or a dessert,
to like or dislike the recipes proposed and to see the explications of the website.
The user can also see the recommended recipes and their details."""
from ast import literal_eval
import streamlit as st
import utils
import user_fooder
import pandas as pd

st.set_page_config(
    page_title="fooder", page_icon="img/fooder_logo2.png", initial_sidebar_state="collapsed"
)

LIKE = False
DISLIKE = False
MAIN = False
DESSERT = False
EXPLICATIONS = False

"""
Page management: handling of the different variables
depending on the user's actions on the website
"""
if not st.session_state:
    st.session_state.raw_recipes = pd.read_csv(
        'data/PP_recipes_data.csv', index_col=0)
if st.session_state.get("like"):
    LIKE, MAIN, DESSERT = True, False, False
    st.session_state.user.add_preferences(
        st.session_state.last_recommended_index, 1)
if st.session_state.get("dislike"):
    DISLIKE, MAIN, DESSERT = True, False, False
    st.session_state.user.add_preferences(
        st.session_state.last_recommended_index, -1)
if st.session_state.get("main"):
    DESSERT, MAIN = False, True
    st.session_state.user = user_fooder.User('main')
if st.session_state.get("dessert"):
    MAIN, DESSERT = False, True
    st.session_state.user = user_fooder.User('dessert')
if st.session_state.get("explications"):
    EXPLICATIONS = True
if st.session_state.get("retour"):
    EXPLICATIONS = False

# Page management: handling of the different pages
MAIN_PAGE = not (EXPLICATIONS) and not (MAIN or DESSERT or LIKE or DISLIKE)
RECOMMENDATION_PAGE = not (EXPLICATIONS) and (
    MAIN or DESSERT or LIKE or DISLIKE)

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
# Page display: First page of the website
if MAIN_PAGE:
    st.title("Fooder")
    st.write(
        """
        <div style="text-align: center;">
            Are you in the mood for a main dish or a dessert? Choose one below:
        </div>
        """,
        unsafe_allow_html=True,
    )
# Management of the sidebar
if RECOMMENDATION_PAGE or MAIN_PAGE:
    st.sidebar.button(
        "Explications", key="explications", help="Explique le fonctionnement du site")
# Page display: Recommendation page
if RECOMMENDATION_PAGE:
    st.session_state.last_recommended_index = st.session_state.user.recipe_suggestion()
    st.title(
        st.session_state.raw_recipes.loc[st.session_state.last_recommended_index]['name'])
    col1, col2, col3 = st.columns(
        [1, 1, 1], gap="small", vertical_alignment="center")
    col1.button("❌", key="dislike", help="Dislike", use_container_width=True)
    col3.button("✅", key="like", help="Like", use_container_width=True)
    images = utils.print_image(
        st.session_state.raw_recipes.loc[st.session_state.last_recommended_index]['name'], 1)[0]
    col2.markdown(
        f"""
            <div style="text-align: center;">
                <img src="{images}" style="height: 200px; object-fit: cover;">
            </div>
            """,
        unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="small")
    col1.text_area("Recipe's steps",
                   '  \n'.join(literal_eval(
                       st.session_state.raw_recipes.loc[
                           st.session_state.last_recommended_index]['steps'])),
                   height=200, disabled=True)
    col2.text_area("Recipe's ingredients",
                   ' \n'.join(literal_eval(
                       st.session_state.raw_recipes.loc[
                           st.session_state.last_recommended_index]['ingredients'])),
                   height=200, disabled=True)
    for (key, preference_value) in reversed(st.session_state.user.get_preferences.items()):
        BUTTON_COLOR = "green" if preference_value == 1 else "red"
        button_html = f"""
        <button style='background-color: {BUTTON_COLOR};
        color: white;padding: 10px; border: none;
        border-radius: 5px; cursor: pointer;'>
            {st.session_state.raw_recipes.loc[key]['name']}
        </button>
        """
        st.sidebar.markdown(button_html, unsafe_allow_html=True)
# Page display: all pages but explications
if not EXPLICATIONS:
    st.write(
        """
    <div style="text-align: center;">
        Choosing a new type of dish will reset your recommendation algorithm
    </div>
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
    col1, col2 = st.columns(2)
    col1.button("Main Dish", key="main")
    col2.button("Dessert", key="dessert")
# Page display: explications page
else:
    st.write(
        """
        Fooder est un site de recommandation de recettes de cuisine. 
        Vous pouvez aimer ou ne pas aimer les recettes qui vous 
        sont proposées pour affiner les recommandations suivantes.
        """
    )
    st.button("Retour", key="retour")
