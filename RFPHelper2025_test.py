import streamlit as st
import pandas as pd
import openai
import re
from io import BytesIO
import os

# ------------------------------------------------------------------------------
# 1) Initialize a "ui_version" in session state if not present.
#    This integer will be appended to widget keys so they refresh when changed.
# ------------------------------------------------------------------------------
if "ui_version" not in st.session_state:
    st.session_state.ui_version = 0

def increment_ui_version():
    """Callback to increment the UI version, effectively resetting widget values."""
    st.session_state.ui_version += 1

# ------------------------------------------------------------------------------
# Streamlit page setup
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Skyhigh Security",
    page_icon="🔒",
    layout="wide"
)

# ------------------------------------------------------------------------------
# OpenAI API Key Setup
# ------------------------------------------------------------------------------
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI API key is missing! Please set it in Streamlit Cloud 'Secrets'.")
else:
    openai.api_key = openai_api_key

# ------------------------------------------------------------------------------
# Set background image
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# Branding and title
# ------------------------------------------------------------------------------
st.title("Skyhigh Security - RFI/RFP AI Tool")

# ------------------------------------------------------------------------------
# Restart Button
# Instead of clearing session state, we just increment ui_version.
# ------------------------------------------------------------------------------
st.button("🔄 Restart", key="restart_button", on_click=increment_ui_version)

# ------------------------------------------------------------------------------
# Dynamic Keys for All Inputs
# The key for each widget includes st.session_state.ui_version.
# When ui_version changes, the widget is "new" and its value resets.
# ------------------------------------------------------------------------------
customer_name = st.text_input(
    "Customer Name",
    key=f"customer_name_{st.session_state.ui_version}"
)

product_choice = st.selectbox(
    "What is the elected product?",
    [
        "Skyhigh Security SSE",
        "Skyhigh Security On-Premise Proxy",
        "Skyhigh Security GAM ICAP",
        "Skyhigh Security CASB",
        "Skyhigh Security Cloud Proxy"
    ],
    key=f"product_choice_{st.session_state.ui_version}"
)

language_choice = st.selectbox(
    "Select language",
    ["English", "French", "Spanish", "German", "Italian"],
    key=f"language_choice_{st.session_state.ui_version}"
)

uploaded_file = st.file_uploader(
    "Upload a CSV or XLS file",
    type=["csv", "xls", "xlsx"],
    key=f"file_uploader_{st.session_state.ui_version}"
)

st.markdown("#### **Select Model for Answer Generation**")
model_choice = st.radio(
    "Choose a model:",
    options=["GPT-4.0", "Due Diligence (Fine-Tuned)"],
    captions=[
        "Recommended option for most technical RFPs/RFIs.",
        "Optimized for Due Diligence and security-related questionnaires."
    ],
    key=f"model_choice_{st.session_state.ui_version}"
)

model_mapping = {
    "GPT-4.0": "gpt-4-turbo",
    "Due Diligence (Fine-Tuned)": "ft:gpt-4o-2024-08-06:personal:skyhigh-due-diligence:BClhZf1W"
}
selected_model = model_mapping[model_choice]

column_location = st.text_input(
    "Specify the location of the questions (e.g., B for column B)",
    key=f"column_location_{st.session_state.ui_version}"
)

optional_question = st.text_input(
    "Extra/Optional: You can ask a unique question here",
    key=f"optional_question_{st.session_state.ui_version}"
)

# ------------------------------------------------------------------------------
# Clean Answer Function
# ------------------------------------------------------------------------------
def clean_answer(answer):
    """
    Removes unwanted formatting and conclusion-like statements.
    Currently, we only remove markdown bold. You can add more filters if needed.
    """
    answer = re.sub(r'\*\*(.*?)\*\*', r'\1', answer)  # Remove markdown bold (`**`)
    return answer.strip()

# ------------------------------------------------------------------------------
# Submit Button
# ------------------------------------------------------------------------------
if st.button("Submit", key=f"submit_button_{st.session_state.ui_version}"):
    responses = []

    # Case 1: Optional single question
    if optional_question:
        questions = [optional_question]

    # Case 2: Multiple questions from uploaded file
    elif customer_name and uploaded_file and column_location:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file, engine="openpyxl")
            
            question_index = ord(column_location.strip().upper()) - ord('A')
            questions = df.iloc[:, question_index].dropna().tolist()
        except Exception as e:
            st.error(f"Error processing file: {e}")
            st.stop()
    else:
        st.warning("Please provide either an optional question or upload a file with questions.")
        st.stop()

    st.success(f"Processing {len(questions)} question(s)...")

    # Generate answers for each question
    for idx, question in enumerate(questions, 1):
        prompt = (
            "You are an expert in Skyhigh Security products, providing highly detailed technical responses for an RFP. "
            "Your answer should be **strictly technical**, sourced **exclusively from official Skyhigh Security documentation**. "
            "Focus on architecture, specifications, security features, compliance, integrations, and standards. "
            "**DO NOT** include disclaimers, introductions, or any mention of knowledge limitations. **Only provide the answer**.\n\n"
            f"Customer: {customer_name}\n"
            f"Product: {product_choice}\n"
            "### Question:\n"
            f"{question}\n\n"
            "### Direct Answer (strictly from official Skyhigh Security documentation):"
        )

        response = openai.ChatCompletion.create(
            model=selected_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.1
        )

        answer = clean_answer(response.choices[0].message.content.strip())
        responses.append(answer)

        # Display each question/answer in an elegant way
        st.markdown(f"""
            <div style="background-color: #1E1E1E; padding: 15px; border-radius: 10px;">
                <h4 style="color: #F5A623;">Q{idx}: {question}</h4>
                <pre style="color: #FFFFFF; white-space: pre-wrap;">{answer}</pre>
            </div><br>
        """, unsafe_allow_html=True)

    # If we processed from a file, allow download of updated file
    if uploaded_file and len(responses) == len(questions):
        df["Answers"] = pd.Series(responses)
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        st.download_button("📥 Download Responses", data=output, file_name="RFP_Responses.xlsx")


