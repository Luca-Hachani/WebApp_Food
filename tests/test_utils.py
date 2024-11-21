import pytest
from webapp_food.utils import print_image, ImageError, update_preferences, fetch_recipe_details
import pandas as pd


def test_search_images_mocked(mocker):
    """Test print_image with a mocked response containing images."""
    mock_html = """
    <html>
        <body>
            <img src="https://gstatic.com/test-image1.jpg"/>
            <img src="https://gstatic.com/test-image2.jpg"/>
        </body>
    </html>
    """
    # Mock the requests.get function
    mocker.patch('requests.get', return_value=type(
        'Response', (object,), {'text': mock_html}))

    # Call the function and verify the output
    images = print_image("mocked term", n=2)
    assert images == ["https://gstatic.com/test-image1.jpg",
                      "https://gstatic.com/test-image2.jpg"]


def test_no_images_found_mocked(mocker):
    """Test print_image with a mocked response containing no images."""
    mock_html = "<html><body></body></html>"
    # Mock the requests.get function
    mocker.patch('requests.get', return_value=type(
        'Response', (object,), {'text': mock_html}))

    # Call the function and expect an ImageError
    with pytest.raises(ImageError):
        print_image("mocked term", n=1)


def test_request_timeout(mocker):
    """Test print_image with a mocked request timeout."""
    # Mock the requests.get function to raise a timeout exception
    mocker.patch('requests.get', side_effect=Exception("Timeout"))

    # Call the function and expect an ImageError
    with pytest.raises(ImageError):
        print_image("mocked term", n=1)


def test_update_preferences(mocker):
    user = mocker.MagicMock()
    update_preferences(user, 1, 1)
    user.add_preferences.assert_called_once_with(1, 1)


def test_fetch_recipe_details():
    data = {
        "steps": ["['Step 1', 'Step 2']"],
        "ingredients": ["['Ingredient 1', 'Ingredient 2']"]
    }
    recipes_df = pd.DataFrame(data)
    steps, ingredients = fetch_recipe_details(recipes_df, 0)
    assert steps == ['Step 1', 'Step 2']
    assert ingredients == ['Ingredient 1', 'Ingredient 2']
