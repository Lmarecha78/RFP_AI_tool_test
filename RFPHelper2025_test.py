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
optional_question = st.text_input("Extra/Optional: You can ask a unique question here")

# Restart Button
def restart_app():
    st.session_state.clear()
    st.rerun()
st.button("🔄 Restart", on_click=restart_app)

# ✅ Function to clean answers (Removes any conclusion, benefits, markdown formatting)
def clean_answer(answer):
    """Removes unwanted formatting and conclusion-like statements."""
    answer = re.sub(r'\*\*(.*?)\*\*', r'\1', answer)  # Remove markdown bold (`**`)
    return answer.strip()

# **Submit Button Logic**
if st.button("Submit"):
    responses = []
    if optional_question:
        questions = [optional_question]
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

    st.success(f"Processing {len(questions)} questions...")

    for idx, question in enumerate(questions, 1):
        prompt = (
            f"You are an expert in Skyhigh Security products, providing highly detailed technical responses for an RFP. "
            f"Your answer should be **strictly technical**, sourced **exclusively from official Skyhigh Security documentation**. "
            f"Focus on architecture, specifications, security features, compliance, integrations, and standards. "
            f"**DO NOT** include disclaimers, introductions, or any mention of knowledge limitations. **Only provide the answer**.\n\n"
            f"Customer: {customer_name}\n"
            f"Product: {product_choice}\n"
            f"### Question:\n{question}\n\n"
            f"### Direct Answer (strictly from official Skyhigh Security documentation):"
        )
        
        response = openai.ChatCompletion.create(
            model=selected_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.1
        )

        answer = clean_answer(response.choices[0].message.content.strip())
        responses.append(answer)
        
        st.markdown(f"""
            <div style="background-color: #1E1E1E; padding: 15px; border-radius: 10px;">
                <h4 style="color: #F5A623;">Q{idx}: {question}</h4>
                <pre style="color: #FFFFFF; white-space: pre-wrap;">{answer}</pre>
            </div><br>
        """, unsafe_allow_html=True)

    if uploaded_file and len(responses) == len(questions):
        df["Answers"] = pd.Series(responses)
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        st.download_button("📥 Download Responses", data=output, file_name="RFP_Responses.xlsx")

