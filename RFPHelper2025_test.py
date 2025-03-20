import streamlit as st
import pandas as pd
import openai
import re
from io import BytesIO
import os

# Streamlit page setup
st.set_page_config(
    page_title="Skyhigh Security",
    page_icon="🔒",
    layout="wide"
)

# ✅ Ensure OpenAI API key is set correctly
openai_api_key = st.secrets.get("OPENAI_API_KEY")

if not openai_api_key:
    st.error("❌ OpenAI API key is missing! Please set it in Streamlit Cloud 'Secrets'.")
else:
    openai.api_key = openai_api_key  # ✅ Correct way to set API key

# Set background image
def set_background(image_url):
    css = f"""
    <style>
    .stApp {{
        background-image: url("{image_url}");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_background("https://raw.githubusercontent.com/lmarecha78/RFP_AI_tool/main/skyhigh_bg.png")

# **Function to Clear All Inputs**
def clear_inputs():
    for key in st.session_state.keys():
        del st.session_state[key]  # Clears session state variables
    st.experimental_rerun()  # Force re-run the app to clear UI

# Branding and title
st.title("Skyhigh Security - RFI/RFP AI Tool")

# Input fields
customer_name = st.text_input("Customer Name", key="customer_name")

product_choice = st.selectbox(
    "What is the elected product?",
    [
        "Skyhigh Security SSE",
        "Skyhigh Security On-Premise Proxy",
        "Skyhigh Security GAM ICAP",
        "Skyhigh Security CASB",
        "Skyhigh Security Cloud Proxy"
    ],
    key="product_choice"
)

language_choice = st.selectbox(
    "Select language",
    ["English", "French", "Spanish", "German", "Italian"],
    key="language_choice"
)

uploaded_file = st.file_uploader("Upload a CSV or XLS file", type=["csv", "xls", "xlsx"], key="uploaded_file")

# **Model Selection**
st.markdown("#### **Select Model for Answer Generation**")
model_choice = st.radio(
    "Choose a model:",
    options=["GPT-4.0", "Due Diligence (Fine-Tuned)"],
    captions=[
        "Recommended option for most technical RFPs/RFIs.",
        "Optimized for Due Diligence and security-related questionnaires."
    ],
    key="model_choice"
)

# Model mapping
model_mapping = {
    "GPT-4.0": "gpt-4-turbo",
    "Due Diligence (Fine-Tuned)": "ft:gpt-4o-2024-08-06:personal:skyhigh-due-diligence:BClhZf1W"
}
selected_model = model_mapping[model_choice]

column_location = st.text_input("Specify the location of the questions (e.g., B for column B)", key="column_location")
answer_column = st.text_input("Optional: Specify the column for answers (e.g., C for column C)", key="answer_column")
optional_question = st.text_input("Extra/Optional: You can ask a unique question here", key="optional_question")

# ✅ **Clear Button**
st.button("Clear", on_click=clear_inputs)


