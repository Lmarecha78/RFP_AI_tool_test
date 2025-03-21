import streamlit as st
import pandas as pd
import openai
import re
from io import BytesIO
import os

# ------------------------------------------------------------------------------
# RESTART LOGIC (working method)
# ------------------------------------------------------------------------------
# If the restart_flag exists and is True, clear session state and immediately rerun.
if "restart_flag" in st.session_state and st.session_state.restart_flag:
    st.session_state.clear()
    st.rerun()

# Initialize restart_flag if not present.
if "restart_flag" not in st.session_state:
    st.session_state.restart_flag = False

def trigger_restart():
    st.session_state.restart_flag = True

# ------------------------------------------------------------------------------
# STREAMLIT PAGE SETUP
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Skyhigh Security",
    page_icon="🔒",
    layout="wide"
)

# ------------------------------------------------------------------------------
# OPENAI API KEY SETUP
# ------------------------------------------------------------------------------
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI API key is missing! Please set it in Streamlit Cloud 'Secrets'.")
else:
    openai.api_key = openai_api_key

# ------------------------------------------------------------------------------
# SET BACKGROUND IMAGE
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
# BRANDING AND TITLE
# ------------------------------------------------------------------------------
st.title("Skyhigh Security - RFI/RFP AI Tool")

# ------------------------------------------------------------------------------
# RESTART BUTTON
# ------------------------------------------------------------------------------
st.button("🔄 Restart", key="restart_button", on_click=trigger_restart)

# ------------------------------------------------------------------------------
# READ CURRENT VALUES FROM SESSION STATE
# ------------------------------------------------------------------------------
# (These keys are used by the input widgets below.)
customer_name_val = st.session_state.get("customer_name", "").strip()
uploaded_file_val = st.session_state.get("uploaded_file", None)
column_location_val = st.session_state.get("column_location", "").strip()
unique_question_val = st.session_state.get("unique_question", "").strip()

# ------------------------------------------------------------------------------
# DETERMINE WHICH FIELDS SHOULD BE DISABLED
# ------------------------------------------------------------------------------
# If any multi-question field is non-empty, disable the unique question.
disable_unique = bool(customer_name_val or uploaded_file_val or column_location_val)
# If the unique question field is non-empty, disable the multi-question fields.
disable_multi = bool(unique_question_val)

# ------------------------------------------------------------------------------
# USER INPUT FIELDS WITH DISTINCT KEYS
# ------------------------------------------------------------------------------
customer_name = st.text_input(
    "Customer Name",
    key="customer_name",
    disabled=disable_multi
)

uploaded_file = st.file_uploader(
    "Upload a CSV or XLS file",
    type=["csv", "xls", "xlsx"],
    key="uploaded_file",
    disabled=disable_multi
)

column_location = st.text_input(
    "Specify the location of the questions (e.g., B for column B)",
    key="column_location",
    disabled=disable_multi
)

unique_question = st.text_input(
    "Extra/Optional: You can ask a unique question here",
    key="unique_question",
    disabled=disable_unique
)

# ------------------------------------------------------------------------------
# MODEL SELECTION
# ------------------------------------------------------------------------------
st.markdown("#### **Select Model for Answer Generation**")
model_choice = st.radio(
    "Choose a model:",
    options=["GPT-4.0", "Due Diligence (Fine-Tuned)"],
    captions=[
        "Recommended option for most technical RFPs/RFIs.",
        "Optimized for Due Diligence and security-related questionnaires."
    ]
)

model_mapping = {
    "GPT-4.0": "gpt-4-turbo",
    "Due Diligence (Fine-Tuned)": "ft:gpt-4o-2024-08-06:personal:skyhigh-due-diligence:BClhZf1W"
}
selected_model = model_mapping[model_choice]

# ------------------------------------------------------------------------------
# CLEAN ANSWER FUNCTION
# ------------------------------------------------------------------------------
def clean_answer(answer):
    """Remove markdown bold formatting from the answer."""
    return re.sub(r'\*\*(.*?)\*\*', r'\1', answer).strip()

# ------------------------------------------------------------------------------
# SUBMIT BUTTON LOGIC
# ------------------------------------------------------------------------------
if st.button("Submit", key="submit_button"):
    responses = []

    # CASE 1: Unique question approach
    if unique_question:
        questions = [unique_question]

    # CASE 2: Multi-question approach
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
        st.warning("Please provide either a unique question OR all of the multi-question fields (Customer Name, File, and Column).")
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
            f"Product: {selected_model}\n"
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

        st.markdown(f"""
            <div style="background-color: #1E1E1E; padding: 15px; border-radius: 10px;">
                <h4 style="color: #F5A623;">Q{idx}: {question}</h4>
                <pre style="color: #FFFFFF; white-space: pre-wrap;">{answer}</pre>
            </div><br>
        """, unsafe_allow_html=True)

    # If questions were loaded from a file, allow downloading the responses.
    if uploaded_file and len(responses) == len(questions):
        df["Answers"] = pd.Series(responses)
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        st.download_button("📥 Download Responses", data=output, file_name="RFP_Responses.xlsx")


