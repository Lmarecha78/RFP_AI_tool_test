import streamlit as st
import pandas as pd
import openai
import re
import os
from io import BytesIO

# Streamlit page setup
st.set_page_config(
    page_title="Skyhigh Security - RFI/RFP AI Tool",
    page_icon="🔒",
    layout="wide"
)

# Retrieve API Key
openai_api_key = st.secrets.get("OPENAI_API_KEY")

if not openai_api_key:
    st.error("❌ OpenAI API key is missing! Set it in Streamlit Cloud 'Secrets'.")
    st.stop()

# ✅ Set OpenAI API key correctly
openai.api_key = openai_api_key

# **Set background image**
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

# Branding and title
st.title("🔒 Skyhigh Security - RFI/RFP AI Tool")

# **Preserve State Across Interactions**
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""
if "product_choice" not in st.session_state:
    st.session_state.product_choice = "Skyhigh Security SSE"
if "language_choice" not in st.session_state:
    st.session_state.language_choice = "English"
if "column_location" not in st.session_state:
    st.session_state.column_location = ""
if "answer_column" not in st.session_state:
    st.session_state.answer_column = ""
if "optional_question" not in st.session_state:
    st.session_state.optional_question = ""
if "model_choice" not in st.session_state:
    st.session_state.model_choice = "GPT-4.0"

# **Input Fields**
st.text_input("Customer Name", key="customer_name")

st.selectbox(
    "What is the elected product?",
    ["Skyhigh Security SSE", "Skyhigh Security On-Premise Proxy", "Skyhigh Security GAM ICAP",
     "Skyhigh Security CASB", "Skyhigh Security Cloud Proxy"],
    key="product_choice"
)

st.selectbox("Select language", ["English", "French", "Spanish", "German", "Italian"], key="language_choice")

# **File Upload Section**
uploaded_file = st.file_uploader("Upload a CSV or XLS file", type=["csv", "xls", "xlsx"])

# ✅ Store the file in session_state if uploaded
if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file
elif st.session_state.uploaded_file:
    st.success(f"📂 File retained: {st.session_state.uploaded_file.name}")

# **Model Selection**
st.markdown("#### **Select Model for Answer Generation**")
st.radio(
    "Choose a model:",
    ["GPT-4.0", "Due Diligence (Fine-Tuned)"],
    key="model_choice",
    captions=[
        "Recommended for technical RFPs/RFIs.",
        "Optimized for Due Diligence and security-related questionnaires."
    ]
)

# **Additional Inputs**
st.text_input("Specify the location of the questions (e.g., B for column B)", key="column_location")
st.text_input("Optional: Specify the column for answers (e.g., C for column C)", key="answer_column")
st.text_input("Extra/Optional: You can ask a unique question here", key="optional_question")

# **Submit Button**
if st.button("Submit"):
    st.success("✅ Processing request...")

    # **Check if either a file is uploaded OR a manual question is provided**
    if not st.session_state.uploaded_file and not st.session_state.optional_question:
        st.error("❌ Please upload a file OR enter a unique question before submitting!")
    else:
        st.success("🚀 Submission accepted! Generating response...")

        # ✅ Simulate AI Response (Replace with OpenAI API call)
        st.write("🔍 Generating AI response...")
        st.write("✅ Response successfully generated!")


