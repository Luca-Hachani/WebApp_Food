""" This module contains utility functions for the webapp_food module.
    The functions are used to search for recipe images on Google."""
from ast import literal_eval
import re
import requests
from bs4 import BeautifulSoup

# use the requests library to search for images on Google


class ImageError(Exception):
    """Raised when an image cannot be found for a recipe"""


def search_images(search_term):
    """use the requests library to search for images on Google

    Args:
        search_term (string): name of the image to search for
    """
    url = 'https://www.google.com/search?tbm=isch&q=' + search_term
    response = requests.get(url, timeout=5)
    return response.text


def print_image(search_term, n=1):
    """search an image and return a printable image

    Args:
        search_term (string): name of the image to search for
    """
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
            raise ImageError("No image found for this recipe")
        return imgs
    except Exception as exc:
        raise ImageError("No image found for this recipe") from exc


def update_preferences(user, recipe_index, preference_value):
    """Update user preferences based on like or dislike actions."""
    user.add_preferences(recipe_index, preference_value)


def fetch_recipe_details(recipes_df, recipe_index):
    """Fetch recipe details (steps and ingredients)."""
    recipe = recipes_df.loc[recipe_index]
    steps = literal_eval(recipe['steps'])
    ingredients = literal_eval(recipe['ingredients'])
    return steps, ingredients
