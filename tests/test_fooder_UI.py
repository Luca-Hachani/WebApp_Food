import streamlit as st
from webapp_food.fooder import MAIN_PAGE


def test_main_page_rendering(mocker):
    # Mock Streamlit functions
    mocker.patch("streamlit.title")
    mocker.patch("streamlit.write")
    mocker.patch("streamlit.sidebar.button")

    # Simulate the MAIN_PAGE state
    mocker.patch("webapp_food.fooder.MAIN_PAGE", True)

    # Run the app logic for MAIN_PAGE
    if MAIN_PAGE:
        st.title("Fooder")
        st.write(
            """
            <div style="text-align: center;font-size:20px">
                Are you in the mood for a main dish or a dessert?
                Choose one below:<br><br><br>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.sidebar.button("Explanations on the website")

    # Verify that components are called
    st.title.assert_called_once_with("Fooder")
    st.write.assert_called_once()
    st.sidebar.button.assert_called_once_with("Explanations on the website")
