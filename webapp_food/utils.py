""" This module contains utility functions for the webapp_food module.
    The functions are used to search for recipe images on Google,
    Transform graphs from Networkx to pyvis, interact between
    the app and the user class, define errors."""
from ast import literal_eval
import re
import requests
from bs4 import BeautifulSoup
import logging
from pyvis.network import Network

# use the requests library to search for images on Google
logger = logging.getLogger(__name__)


class ImageError(Exception):
    """Raised when an image cannot be found for a recipe"""


class NoNeighborError(Exception):
    """Raised when the user has no near neighbor"""


def search_images(search_term):
    """use the requests library to search for images on Google

    Args:
        search_term (string): name of the image to search for
    """
    logger.debug(f"In search_images with search_term={search_term}")
    url = 'https://www.google.com/search?tbm=isch&q=' + search_term
    response = requests.get(url, timeout=5)
    return response.text


def print_image(search_term, n=1):
    """search an image and return a printable image

    Args:
        search_term (string): name of the image to search for
    """
    logger.debug(f"In print_image with search_term={search_term}")
    try:
        html = search_images(search_term)
        soup = BeautifulSoup(html, 'html.parser')
        img_tags = soup.find_all('img', {'src': re.compile('gstatic.com')})
        imgs = []
        for i, img_tag in enumerate(img_tags):
            if i >= n:
                break
            imgs.append(img_tag['src'])
        if not imgs:
            logger.info("No image found for this recipe")
            raise ImageError("No image found for this recipe")
        return imgs
    except Exception as exc:
        logger.error(f"Error fetching image for recipe {search_term}: {exc}")
        raise ImageError("No image found for this recipe") from exc


def update_preferences(user, recipe_index, preference_value):
    """Update user preferences based on like or dislike actions."""
    logger.debug(f"Updating preferences for user {user} with recipe_index={
                 recipe_index} and preference_value={preference_value}")
    user.add_preferences(recipe_index, preference_value)


def fetch_recipe_details(recipes_df, recipe_index):
    """Fetch recipe details (steps and ingredients)."""
    logger.debug(f"Fetching recipe details for recipe_index={recipe_index}")
    recipe = recipes_df.loc[recipe_index]
    steps = literal_eval(recipe['steps'])
    ingredients = literal_eval(recipe['ingredients'])
    return steps, ingredients


def visualize_graph(graph):
    """
    Saves a NetworkX graph using PyVis.

    Parameters:
    - graph: The NetworkX graph to save.
    """
    logger.debug(f"Visualizing graph with {len(graph.nodes)} \
                 nodes and {len(graph.edges)} edges")
    # Create a PyVis Network object
    net = Network(notebook=True, width="100%",
                  height="300px", cdn_resources='remote')

    # Convert NetworkX graph to PyVis
    net.from_nx(graph)

    # Save the graph as an HTML file
    net.save_graph("webapp_food/graphs/neighbour.html")
