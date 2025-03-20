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

# ✅ **Initialize session state variables**
if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""
if "product_choice" not in st.session_state:
    st.session_state.product_choice = ""
if "language_choice" not in st.session_state:
    st.session_state.language_choice = ""
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "model_choice" not in st.session_state:
    st.session_state.model_choice = "GPT-4.0"
if "column_location" not in st.session_state:
    st.session_state.column_location = ""
if "answer_column" not in st.session_state:
    st.session_state.answer_column = ""
if "optional_question" not in st.session_state:
    st.session_state.optional_question = ""

# ✅ **Clear All Inputs Function**
def clear_inputs():
    """Resets all input fields by clearing session state."""
    st.session_state.clear()
    st.rerun()  # ✅ Force rerun the app after clearing

# Branding and title
st.title("Skyhigh Security - RFI/RFP AI Tool")

# **Clear Button (Resets everything)**
st.button("Clear All Inputs", on_click=clear_inputs)

# **Input Fields**
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

column_location = st.text_input("Specify the location of the questions (e.g., B for column B)", key="column_location")
answer_column = st.text_input("Optional: Specify the column for answers (e.g., C for column C)", key="answer_column")
optional_question = st.text_input("Extra/Optional: You can ask a unique question here", key="optional_question")

# ✅ **Submit Button Logic (Same as before)**
if st.button("Submit"):
    st.info(f"Processing request for: {optional_question if optional_question else 'uploaded file'}")

