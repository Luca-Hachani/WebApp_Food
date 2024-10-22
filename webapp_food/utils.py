import pandas as pd
import re
import logging
import requests
from IPython.display import Image
from bs4 import BeautifulSoup


# use the requests library to search for images on Google


def search_images(search_term):
    """use the requests library to search for images on Google

    Args:
        search_term (string): name of the image to search for
    """
    url = 'https://www.google.com/search?tbm=isch&q=' + search_term
    response = requests.get(url, timeout=5)
    return response.text


def return_image(search_term, n=1):
    """return n image from Google search results

    Args:
        search_term (string): name of the image to search for
        n (int): number of images to return (default: {1})

    Returns:
        list: list of image urls
    """
    logging.info("Searching for image: %s", search_term)
    imgs = []
    try:
        html = search_images(search_term)
    except requests.RequestException as e:
        logging.error("Error while requesting Google for the image: %s", e)
    else:
        soup = BeautifulSoup(html, 'html.parser')
        img_tags = soup.find_all('img', {'src': re.compile('gstatic.com')})
        for i, img_tag in enumerate(img_tags):
            if i >= n:
                logging.info(
                    "Found only %d images for search term: %s", i, search_term)
                break
            imgs.append(Image(img_tag['src']))
        if not imgs:
            logging.error("No images found for search term: %s", search_term)
    return imgs


def load_recipe_dataset():
    """Load the raw recipe dataset from the CSV file.

    Returns:
        pd.Dataframe: raw recipe dataset
    """
    dataset = pd.read_csv('data/RAW_recipes.csv')
    return dataset


def get_recipe(index):
    """return the recipe with the given index.

    Args:
        index (int): index of the recipe to return

    Returns:
        pd.Dataframe: line of the recipe dataset with the given index
    """
    dataset = load_recipe_dataset()
    return dataset[dataset['id'] == index]
