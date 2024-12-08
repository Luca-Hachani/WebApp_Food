"""
This module contains utility functions for the `webapp_food` module.

The functions include:
- Searching for recipe images on Google.
- Transforming graphs from NetworkX to PyVis.
- Interacting between the app and the User class.
- Defining custom exceptions for specific errors.
"""
from ast import literal_eval
import re
import requests
from bs4 import BeautifulSoup
import logging
from pyvis.network import Network
from webapp_food.settings import RECIPE_COLUMNS

# use the requests library to search for images on Google
logger = logging.getLogger(__name__)


class ImageError(Exception):
    """
    Raised when an image cannot be found for a recipe
    """


class NoNeighborError(Exception):
    """
    Raised when the user has no near neighbor
    """


def search_images(search_term: str) -> str:
    """
    Uses the requests library to search for images on Google.

    Parameters
    ----------
    search_term : str
        The name or term to search for images.

    Returns
    -------
    str
        The HTML content of the Google Images search results.

    Notes
    -----
    - The search is performed by making a GET request to Google Images.
    - This function does not parse or process the returned HTML; it simply
      fetches the response.

    Example
    -------
    >>> html_content = search_images("chocolate cake")
    >>> print(html_content[:100])  # Print the first 100 characters
    """
    logger.debug(f"In search_images with search_term={search_term}")
    url = 'https://www.google.com/search?tbm=isch&q=' + search_term
    response = requests.get(url, timeout=5)
    return response.text


def print_image(search_term: str, n: int = 1) -> list:
    """
    Searches for an image and returns a printable URL.

    Parameters
    ----------
    search_term : str
        The name or term to search for images.
    n : int, optional
        The number of images to fetch, by default 1.

    Returns
    -------
    list of str
        A list of image URLs.

    Raises
    ------
    ImageError
        If no images are found or an error occurs during the search.

    Example
    -------
    >>> images = print_image("chocolate cake", n=1)
    >>> print(images)
    ['https://example.com/image.jpg']
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


def update_preferences(user, recipe_index: int,
                       preference_value: int) -> None:
    """
    Updates user preferences based on like or dislike actions.

    Parameters
    ----------
    user : User
        The user object to update preferences for.
    recipe_index : int
        The index of the recipe to update preferences for.
    preference_value : int
        The preference value to assign (e.g., +1 for like, -1 for dislike).

    Example
    -------
    >>> update_preferences(user, recipe_index=42, preference_value=1)
    """
    logger.debug(f"Updating preferences for user {user} with recipe_index={
                 recipe_index} and preference_value={preference_value}")
    user.add_preferences(recipe_index, preference_value)


def fetch_recipe_details(recipes_df, recipe_index: int) -> tuple[list, list]:
    """
    Fetches recipe details including steps and ingredients.

    Parameters
    ----------
    recipes_df : pd.DataFrame
        The DataFrame containing recipe information.
    recipe_index : int
        The index of the recipe to fetch details for.

    Returns
    -------
    tuple of list
        A tuple containing two lists:
        - steps : list of str
            The steps required to prepare the recipe.
        - ingredients : list of str
            The ingredients needed for the recipe.

    Example
    -------
    >>> steps, ingredients = fetch_recipe_details(recipes_df, recipe_index=42)
    >>> print(steps)
    ['Step 1', 'Step 2']
    >>> print(ingredients)
    ['Ingredient 1', 'Ingredient 2']
    """
    logger.debug(f"Fetching recipe details for recipe_index={recipe_index}")
    recipe = recipes_df.loc[recipe_index]
    steps = literal_eval(recipe[RECIPE_COLUMNS[2]])
    ingredients = literal_eval(recipe[RECIPE_COLUMNS[4]])
    return steps, ingredients


def visualize_graph(graph) -> None:
    """
    Saves a NetworkX graph as an interactive PyVis HTML visualization.

    Parameters
    ----------
    graph : networkx.Graph
        The NetworkX graph to visualize.

    Notes
    -----
    - The graph is saved as an HTML file at
      `webapp_food/graphs/neighbour.html`.
    - The PyVis library is used to create an interactive graph.

    Example
    -------
    >>> import networkx as nx
    >>> G = nx.erdos_renyi_graph(10, 0.5)
    >>> visualize_graph(G)
    # The graph visualization is saved in the specified HTML file.
    """
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
