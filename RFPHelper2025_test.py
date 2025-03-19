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

# Retrieve OpenAI API key from Streamlit Secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")

if not openai_api_key:
    st.error("❌ OpenAI API key is missing! Please set it in Streamlit Cloud 'Secrets'.")
    st.stop()  # Stop execution if API key is missing

# ✅ Set OpenAI API key correctly
openai.api_key = openai_api_key

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

# Branding and title
st.title("Skyhigh Security - RFI/RFP AI Tool")

# Input fields
customer_name = st.text_input("Customer Name")

product_choice = st.selectbox(
    "What is the elected product?",
    [
        "Skyhigh Security SSE",
        "Skyhigh Security On-Premise Proxy",
        "Skyhigh Security GAM ICAP",
        "Skyhigh Security CASB",
        "Skyhigh Security Cloud Proxy"
    ]
)

language_choice = st.selectbox(
    "Select language",
    ["English", "French", "Spanish", "German", "Italian"]
)

uploaded_file = st.file_uploader("Upload a CSV or XLS file", type=["csv", "xls", "xlsx"])

# **Model Selection**
st.markdown("#### **Select Model for Answer Generation**")
model_choice = st.radio(
    "Choose a model:",
    options=["GPT-4.0", "Due Diligence (Fine-Tuned)"],
    captions=[
        "Recommended option for most technical RFPs/RFIs.",
        "Optimized for Due Diligence and security-related questionnaires."
    ]
)

# Model mapping
model_mapping = {
    "GPT-4.0": "gpt-4-turbo",
    "Due Diligence (Fine-Tuned)": "ft:gpt-4o-2024-08-06:personal:skyhigh-due-diligence:BClhZf1W"
}
selected_model = model_mapping[model_choice]

column_location = st.text_input("Specify the location of the questions (e.g., B for column B)")
answer_column = st.text_input("Optional: Specify the column for answers (e.g., C for column C)")
optional_question = st.text_input("Extra/Optional: You can ask a unique question here")

# Function to clean AI-generated answers
def clean_answer(answer):
    return re.sub(r'(Overall,.*|In conclusion.*|Conclusion:.*)', '', answer, flags=re.IGNORECASE | re.DOTALL).strip()

# ✅ Use `st.session_state` to preserve state
if "answer" not in st.session_state:
    st.session_state.answer = ""
if "show_correction" not in st.session_state:
    st.session_state.show_correction = False
if "user_feedback" not in st.session_state:
    st.session_state.user_feedback = None

# **Submit Button Logic**
if st.button("Submit"):
    if optional_question:
        prompt = (
            f"You are an expert in Skyhigh Security products, providing highly detailed technical responses for an RFP. "
            f"Your answer should be **strictly technical**, focusing on architecture, specifications, security features, compliance, integrations, and standards. "
            f"**DO NOT** include disclaimers, introductions, or any mention of knowledge limitations. **Only provide the answer**.\n\n"
            f"Customer: {customer_name}\n"
            f"Product: {product_choice}\n"
            f"### Question:\n{optional_question}\n\n"
            f"### Direct Answer (no intro, purely technical):"
        )

        response = openai.ChatCompletion.create(
            model=selected_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.1
        )

        st.session_state.answer = clean_answer(response.choices[0].message["content"].strip())

# Display answer if available
if st.session_state.answer:
    st.markdown(f"### Your Question: {optional_question}")
    st.write(st.session_state.answer)

    # **Feedback Mechanism**
    feedback = st.radio("Is this answer correct?", ["Yes", "No"], key="feedback")

    if feedback == "No":
        st.session_state.show_correction = True  # ✅ Preserve correction state

    if st.session_state.show_correction:
        correction = st.text_area("Provide the correct information or missing details:", key="correction")

        if st.button("Submit Correction"):
            corrected_prompt = (
                f"The following AI-generated response was marked as incorrect by a user. "
                f"Revise it based on the user's correction while ensuring accuracy, completeness, and technical depth.\n\n"
                f"**Original Question:** {optional_question}\n"
                f"**Original AI Answer:** {st.session_state.answer}\n"
                f"**User Correction:** {correction}\n\n"
                f"### Updated Answer:"
            )

            revised_response = openai.ChatCompletion.create(
                model=selected_model,
                messages=[{"role": "user", "content": corrected_prompt}],
                max_tokens=800,
                temperature=0.1
            )

            st.session_state.answer = clean_answer(revised_response.choices[0].message["content"].strip())

            st.markdown("### ✅ Updated Answer:")
            st.write(st.session_state.answer)


