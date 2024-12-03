""" Main file of the web application.
It allows the user to choose between a main dish or a dessert,
to like or dislike the recipes proposed and
to see the graph of adjency for the current user.
The user can also see the recommended recipes and their details."""
import streamlit as st
from webapp_food.utils import update_preferences, print_image, \
    ImageError, fetch_recipe_details, visualize_graph
from webapp_food.user_fooder import User
import pandas as pd
import logging
from webapp_food.settings import COLORS, LIKE, DISLIKE

# Page configuration
st.set_page_config(
    page_title="fooder", page_icon="img/fooder_logo2.png",
    initial_sidebar_state="collapsed"
)

# Page state variables
GRAPH_VIZ = HISTORY = False

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
                       st.session_state.last_recommended_index, LIKE)

if st.session_state.get("dislike"):
    logging.debug("Dislike button clicked")
    update_preferences(st.session_state.user,
                       st.session_state.last_recommended_index, DISLIKE)

if st.session_state.get("main"):
    logging.debug("Main button clicked")
    st.session_state.user = User('main')

if st.session_state.get("dessert"):
    logging.debug("Dessert button clicked")
    st.session_state.user = User('dessert')

if st.session_state.get("graph"):
    logging.debug("Graph button clicked")
    GRAPH_VIZ = True
    st.session_state.graph_type = LIKE

if st.session_state.get("dislike_graph"):
    logging.debug("Dislike graph button clicked")
    st.session_state.graph_type = DISLIKE
    GRAPH_VIZ = True

if st.session_state.get("like_graph"):
    logging.debug("Like graph button clicked")
    st.session_state.graph_type = LIKE
    GRAPH_VIZ = True

if st.session_state.get("back"):
    logging.debug("Back button clicked")
    GRAPH_VIZ = False
    if st.session_state.get("user"):
        if st.session_state.get("user").get_type_of_dish == 'main':
            MAIN = True
        else:
            DESSERT = True

# Page management: handling of the different pages
MAIN_PAGE = not (GRAPH_VIZ) and not (st.session_state.get("user"))
RECOMMENDATION_PAGE = not (GRAPH_VIZ) and (
    st.session_state.get("user"))

# Page management: different styles for the website
# removing padding
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
# title style
st.markdown(
    f"""
    <style>
    h1 {{
        text-align: center;
        color: {COLORS['first_color']};
        height: 150px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)
# button style
st.markdown(
    """
        <style>
        div.stButton {
            display: flex;
            justify-content: center;
            color: COLORS['second_color'];
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
        "Click here to show  \nyour user adjency graph", key="graph",
        help="Explain website's algorithm and dataset used")
# Management of History
if st.session_state.get("user") and not GRAPH_VIZ:
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
if not GRAPH_VIZ:
    col1, col2 = st.columns(2)
    col1.button("Main Dish", key="main")
    col2.button("Dessert", key="dessert")
# Page display: graph page
else:
    st.write(
        """
        Fooder is a food recommendation website.
        You can like or dislike the recipes proposed to you
        to update the next food recommendation.
        """
    )
    st.sidebar.button("Back", key="back")
    col1, col2 = st.columns([4, 2], gap="small")
    graph_to_plot = st.session_state.user.get_graph(
        st.session_state.graph_type)
    visualize_graph(graph_to_plot)
    with open("webapp_food/graphs/neighbour.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    with col1:
        st.components.v1.html(html_content, height=500)
        col11, col12 = st.columns(2)
        col11.button('Graph of Likes neighboors', key='like_graph')
        col12.button('Graph of Dislikes neighboors', key='dislike_graph')
    with col2:
        st.write(
            """
            <div style="text-align: center;">
                <br><br><br><br>
                The graph shows the relationships between you and other users.
                <br><br>
            </div>
            """,
            unsafe_allow_html=True,
        )
# At the end of the page, put the logo centered
col1, col2, col3, col4, col5 = st.columns(5)
col3.image("img/fooder_logo2.png", use_container_width=True)
