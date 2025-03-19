import streamlit as st
import pandas as pd
import openai
import requests
import json
import re
from io import BytesIO

# 🔹 Streamlit page setup
st.set_page_config(page_title="Skyhigh Security - AI RFP Tool", page_icon="🔒", layout="wide")

# 🔹 Authentication Credentials
PASSWORD = "Skyhigh@2025!"  # Change this to your secure password

# 🔹 Function for Authentication
def authenticate():
    """Check user authentication and store the result in session state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔒 Skyhigh Security RFP Tool")
        st.subheader("Enter Password to Access")

        password_input = st.text_input("Password", type="password")

        if st.button("Login"):
            if password_input == PASSWORD:
                st.session_state.authenticated = True
                st.success("✅ Authentication successful! Access granted.")
                st.rerun()  
            else:
                st.error("❌ Incorrect password. Try again.")

        st.stop()

# ✅ Call authentication function
authenticate()

# 🔹 Retrieve API Keys Securely from Streamlit Secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")
github_token = st.secrets.get("GITHUB_TOKEN")

# 🔹 GitHub Gist Information
GITHUB_GIST_URL = "https://gist.githubusercontent.com/Lmarecha78/raw/96e4473a6d441bda6794e11d4a74b93b/corrections.json"
GITHUB_GIST_ID = "96e4473a6d441bda6794e11d4a74b93b"

# 🔹 Load corrections from GitHub Gist
def load_corrections():
    try:
        response = requests.get(GITHUB_GIST_URL)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

# 🔹 Save corrections to GitHub Gist securely
def save_corrections(corrections):
    if not github_token:
        st.error("❌ GitHub Token is missing! Set it in Streamlit Cloud 'Secrets'.")
        return False

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "files": {
            "corrections.json": {"content": json.dumps(corrections, indent=4)}
        }
    }
    response = requests.patch(f"https://api.github.com/gists/{GITHUB_GIST_ID}", headers=headers, json=payload)
    return response.status_code == 200

# 🔹 Initialize session state for corrections
if "corrections" not in st.session_state:
    st.session_state.corrections = load_corrections()

if "correcting_question" not in st.session_state:
    st.session_state.correcting_question = None

# 🔹 Check API Key
if not openai_api_key:
    st.error("❌ OpenAI API key is missing! Set it in Streamlit Cloud 'Secrets'.")
    st.stop()

# 🔹 OpenAI Client Initialization
import openai
openai.api_key = openai_api_key

# 🔹 Function to clean AI responses
def clean_answer(answer):
    return re.sub(r'(Overall,.*|In conclusion.*|Conclusion:.*)', '', answer, flags=re.IGNORECASE | re.DOTALL).strip()

# 🔹 Set Background
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

# 🔹 User Inputs
st.title("Skyhigh Security - RFI/RFP AI Tool")

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

language_choice = st.selectbox("Select language", ["English", "French", "Spanish", "German", "Italian"])
uploaded_file = st.file_uploader("Upload a CSV or XLS file", type=["csv", "xls", "xlsx"])

# 🔹 Model selection (RESTORED)
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

# 🔹 Processing User Questions
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

        response = openai_client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.1
        )

        answer = clean_answer(response.choices[0].message.content.strip())

        st.markdown(f"### Your Question: {optional_question}")
        st.write(answer)

        # **Feedback Mechanism**
        feedback = st.radio("Is this answer correct?", ["Yes", "No"])
        
        if feedback == "No":
            correction = st.text_area("Provide the correct information or missing details:")
            if st.button("Submit Correction"):
                corrected_prompt = (
                    f"The following AI-generated response was marked as incorrect by a user. "
                    f"Revise it based on the user's correction while ensuring accuracy, completeness, and technical depth.\n\n"
                    f"**Original Question:** {optional_question}\n"
                    f"**Original AI Answer:** {answer}\n"
                    f"**User Correction:** {correction}\n\n"
                    f"### Updated Answer:"
                )

                revised_response = openai_client.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": corrected_prompt}],
                    max_tokens=800,
                    temperature=0.1
                )

                revised_answer = clean_answer(revised_response.choices[0].message.content.strip())
                
                st.markdown("### ✅ Updated Answer:")
                st.write(revised_answer)

# 🔹 Correction Input UI
if st.session_state.correcting_question:
    question = st.session_state.correcting_question
    st.warning(f"Please provide the correct answer for: **{question}**")
    corrected_input = st.text_area("Your Correct Answer", key=f"text_{hash(question)}")

    if st.button("Save Correction"):
        if corrected_input:
            st.session_state.corrections[question] = corrected_input
            save_corrections(st.session_state.corrections)
            st.success("✅ Correction saved!")
            st.session_state.correcting_question = None
            st.rerun()
        else:
            st.error("Correction cannot be empty.")
