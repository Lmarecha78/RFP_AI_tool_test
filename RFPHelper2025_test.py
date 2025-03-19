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

# 🔹 Check API Key
if not openai_api_key:
    st.error("❌ OpenAI API key is missing! Set it in Streamlit Cloud 'Secrets'.")
    st.stop()

# 🔹 OpenAI Client Initialization
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=openai_api_key)
    new_api = True
except ImportError:
    openai.api_key = openai_api_key
    openai_client = openai
    new_api = False

# 🔹 Function to clean AI responses
def clean_answer(answer):
    return re.sub(r'(Overall,.*|In conclusion.*|Conclusion:.*)', '', answer, flags=re.IGNORECASE | re.DOTALL).strip()

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

uploaded_file = st.file_uploader("Upload a CSV or XLS file", type=["csv", "xls", "xlsx"])
optional_question = st.text_input("Ask a unique question")

# 🔹 Processing User Questions (File or Unique)
if st.button("Submit"):
    if optional_question:
        question_list = [optional_question]
    elif uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        question_list = df.iloc[:, 0].dropna().tolist()  # Assuming questions are in the first column
    else:
        st.error("Please enter a question or upload a file.")
        st.stop()

    answers = []
    for question in question_list:
        # Check if correction exists
        corrected_answer = st.session_state.corrections.get(question, None)

        if corrected_answer:
            answer = corrected_answer
            st.success("✅ Retrieved from previous corrections.")
        else:
            # Generate answer using OpenAI
            prompt = f"Provide a technical response for {product_choice} regarding:\n\n{question}"
            if new_api:
                response = openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800
                )
            else:
                response = openai_client.ChatCompletion.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800
                )

            answer = clean_answer(response.choices[0].message.content.strip())

        # Show Answer
        st.markdown(f"### Q: {question}")
        st.write(answer)

        # Allow User to Provide Feedback
        col1, col2 = st.columns(2)

        with col1:
            if st.button(f"👍 Correct - {question}", key=f"correct_{question}"):
                st.success("Thank you for your feedback!")

        with col2:
            if st.button(f"👎 Incorrect - {question}", key=f"incorrect_{question}"):
                st.warning("Please provide the correct answer:")
                corrected_input = st.text_area(f"Your Correct Answer - {question}", key=f"text_{question}")

                if st.button(f"Save Correction - {question}", key=f"save_{question}"):
                    if corrected_input:
                        # Save Correction
                        st.session_state.corrections[question] = corrected_input
                        success = save_corrections(st.session_state.corrections)
                        if success:
                            st.success("✅ Correction saved to GitHub Gist!")
                        else:
                            st.error("❌ Failed to save correction. Check GitHub Token.")
                    else:
                        st.error("Correction cannot be empty.")

        answers.append(answer)

