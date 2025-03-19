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
openai_api_key = st.secrets.get("OPENAI_API_KEY")  # Use .get() to avoid crashes

if not openai_api_key:
    st.error("❌ OpenAI API key is missing! Please set it in Streamlit Cloud 'Secrets'.")
    st.stop()  # Stop execution if API key is missing

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=openai_api_key)  # ✅ Now it's correctly defined

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
        feedback = st.radio("Is this answer correct?", ["Yes", "No"], key="feedback")

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

    elif customer_name and uploaded_file and column_location:
        try:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file, engine="openpyxl")

            # Convert column letters to index
            question_index = ord(column_location.strip().upper()) - ord('A')
            questions = df.iloc[:, question_index].dropna().tolist()

            st.success(f"Extracted {len(questions)} questions for '{customer_name}'. Generating responses...")

            answers = []
            for idx, question in enumerate(questions, 1):
                prompt = (
                    f"You are an expert in Skyhigh Security products, responding to an RFP for customer '{customer_name}'. "
                    f"Provide a detailed, precise, and technical response sourced explicitly from official Skyhigh Security documentation. "
                    f"**Do NOT include introductions or disclaimers.**\n\n"
                    f"Product: {product_choice}\n"
                    f"### Question:\n{question}\n\n"
                    f"### Direct Technical Answer:"
                )

                response = openai_client.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.1
                )

                answer = clean_answer(response.choices[0].message.content.strip())
                answers.append(answer)

                st.markdown(f"### Q{idx}: {question}")
                st.write(answer)

        except Exception as e:
            st.error(f"Error processing file: {e}")

    else:
        st.error("Please fill in all mandatory fields and upload a file or enter an optional question.")
