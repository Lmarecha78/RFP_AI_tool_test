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
                st.rerun()  # ✅ Fixed: Replaced `st.experimental_rerun()` with `st.rerun()`
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
    st.session_state.correcting_question = None  # ✅ Track the question being corrected

if "correction_input_visible" not in st.session_state:
    st.session_state.correction_input_visible = False  # ✅ Track if the correction input should be shown

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

set_background("https://raw.githubusercontent.com/Lmarecha78/RFP_AI_tool/main/skyhigh_bg.png")

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

optional_question = st.text_input("Ask a unique question")

# 🔹 Processing User Questions
if st.button("Submit"):
    st.session_state.correction_input_visible = False  # ✅ Reset correction input state

    if optional_question:
        question = optional_question
    else:
        st.error("Please enter a question.")
        st.stop()

    corrected_answer = st.session_state.corrections.get(question, None)

    if corrected_answer:
        answer = corrected_answer
        st.success("✅ Retrieved from previous corrections.")
    else:
        prompt = f"Provide a technical response for {product_choice} regarding:\n\n{question}"
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        answer = clean_answer(response.choices[0].message.content.strip())

    st.markdown(f"### 📝 Response for: **{question}**")
    st.write(answer)

    # ✅ Show Correction Button Without Resetting the Page
    if st.button(f"👎 Incorrect - {question}", key=f"incorrect_{hash(question)}"):
        st.session_state.correcting_question = question
        st.session_state.correction_input_visible = True  # ✅ Show input immediately

# 🔹 Show Correction Input Immediately When "Incorrect" Is Clicked
if st.session_state.correction_input_visible and st.session_state.correcting_question:
    question = st.session_state.correcting_question
    st.warning(f"📝 Provide a corrected answer for: **{question}**")

    with st.form(key="correction_form"):
        corrected_input = st.text_area("Your Correct Answer", key=f"text_{hash(question)}")
        submit_button = st.form_submit_button("Save Correction")

        if submit_button:
            if corrected_input:
                st.session_state.corrections[question] = corrected_input
                save_corrections(st.session_state.corrections)
                st.success("✅ Correction saved to GitHub Gist!")
                st.session_state.correction_input_visible = False
            else:
                st.error("⚠️ Correction cannot be empty.")

