"""
Main file of the web application.

This module manages the main functionality of the Fooder web application,
including:
- Choosing between main dishes and desserts.
- Liking or disliking recommended recipes.
- Viewing the graph of adjency for the current user.
- Displaying recommended recipes and their details.
"""

import streamlit as st
from webapp_food.utils import update_preferences, print_image, \
    ImageError, fetch_recipe_details, visualize_graph, NoNeighborError
from webapp_food.user_fooder import User
import pandas as pd
import logging
from webapp_food.settings import COLORS, LIKE, DISLIKE, \
    RECIPE_COLUMNS, RECIPE_DF
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="fooder", page_icon="img/fooder_logo2.png",
    initial_sidebar_state="collapsed"
)

# Page state variables
GRAPH_VIZ = HISTORY = GRAPH_ERROR = False

"""
Page management: handling of the different variables
depending on the user's actions on the website
"""
if not st.session_state:
    st.session_state.raw_recipes = pd.read_csv(
        RECIPE_DF, index_col=0)
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
    if st.session_state.get("user"):
        GRAPH_VIZ = True
        st.session_state.graph_type = LIKE
    else:
        GRAPH_ERROR = True

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
    if GRAPH_ERROR:
        st.sidebar.write(
            "You need to like or dislike a recipe before accessing the graph")
# Management of History
if st.session_state.get("user") and not GRAPH_VIZ:
    st.sidebar.write("History of your preferences:")
    for (key, preference_value) in reversed(
            st.session_state.user.get_preferences.items()):
        if st.sidebar.button(st.session_state.raw_recipes.loc[key]
                             [RECIPE_COLUMNS[1]] + "  \nRating: " +
                             str(preference_value), key=key):
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
            st.session_state.last_recommended_index][RECIPE_COLUMNS[1]])
    col1, col2, col3 = st.columns(
        [1, 1, 1], gap="small", vertical_alignment="center")
    col1.button("❌", key="dislike", help="Dislike", use_container_width=True)
    col3.button("✅", key="like", help="Like", use_container_width=True)
    try:
        images = print_image(
            st.session_state.raw_recipes.loc[
                st.session_state.last_recommended_index]
            [RECIPE_COLUMNS[1]], 1)[0]
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
    st.session_state.last_recommended_index = \
        st.session_state.user.recipe_suggestion()
    st.write(
        f"""
        <div style="text-align: justify; font-size:20px; color:\
        {COLORS['first_color']}; font-weight: bold">
        Fooder is a food recommendation website based
        on a nearest neighbors algorithm.
        Next recipe is recommended in function of your nearest neighbors,
        depending on you and the other users likes and dislikes.
        Other users's preferences come from a dataset of recipes
        leaked from Fooder.com. On this page you can see your adjency
        graph with the users that are closest to you, as well as
        the number of recipes they can still recommend to you.
        <br><br>
        </div>
        """, unsafe_allow_html=True)
    st.sidebar.button("Back", key="back")
    col1, col2 = st.columns([2, 2], gap="small")
    try:
        graph_to_plot = st.session_state.user.get_graph(
            st.session_state.graph_type)
    except NoNeighborError as e:
        logging.info(e)
        st.write(
            """
            <div style="text-align: center; font-size:30px">
                <br><br><br><br>
                You have not yet liked or disliked any recipe, <br>
                or you have no near neighbors in the database
                from your current preferences.
                <br><br>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        visualize_graph(graph_to_plot)
        with open("webapp_food/graphs/neighbour.html", "r",
                  encoding="utf-8") as f:
            html_content = f.read()
        with col1:
            st.components.v1.html(html_content, height=300)
            col11, col12 = st.columns(2)
            col11.button('Graph of Likes neighbors', key='like_graph')
            col12.button('Graph of Dislikes neighbors', key='dislike_graph')
        with col2:
            neighbors_data = st.session_state.user.get_neighbor_data(
                st.session_state.graph_type)
            neighbors_data.insert(0, 'User', neighbors_data.index)
            fig = go.Figure(data=[go.Table(
                columnwidth=[1] * len(neighbors_data.columns),
                header=dict(values=list(neighbors_data.columns),
                            align='left', font=dict(size=14), height=30),
                cells=dict(values=[neighbors_data[col]
                                   for col in neighbors_data.columns],
                           align='left', font=dict(size=14), height=30)
            )])
            fig.update_layout(margin=dict(t=0))
            st.plotly_chart(fig, use_container_width=True)
# At the end of the page, put the logo centered
col1, col2, col3, col4, col5 = st.columns(5)
col3.image("img/fooder_logo2.png", use_container_width=True)
