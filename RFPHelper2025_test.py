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
answer_column = st.text_input("Optional: Specify the column for answers (e.g., C for column C)")
optional_question = st.text_input("Extra/Optional: You can ask a unique question here")

# ✅ Function to clean answers (Removes any conclusion, benefits, markdown formatting)
def clean_answer(answer):
    """Removes unwanted formatting and conclusion-like statements."""
    answer = re.sub(r'\*\*(.*?)\*\*', r'\1', answer)  # Remove markdown bold (`**`)

    patterns = [
        r'\b(Overall,|In conclusion,|Conclusion:|To summarize,|Thus,|Therefore,|Finally,|This enables|This ensures|This allows|This provides|This results in|By leveraging|By implementing).*',
        r'.*\b(enhancing|improving|achieving|helping to ensure|complying with|ensuring).*security posture.*',
        r'.*\b(this leads to|this results in|which results in|thereby improving|thus ensuring).*',
        r'\b(By using|By adopting|By deploying|By integrating|By utilizing).*',
        r'\b(This approach|This strategy|This technology).*',
    ]
    
    for pattern in patterns:
        answer = re.sub(pattern, '', answer, flags=re.IGNORECASE | re.DOTALL).strip()

    return answer

# ✅ Function to display answers with a Streamlit Copy Button
def display_answer(question, answer, index):
    """Displays each answer with correct formatting and a working copy button."""
    unique_id = f"answer_{index}"  # Unique ID for each answer

    with st.container():
        st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(255, 255, 255, 0.1);">
            <h4 style="color: #F5A623;">Q{index}: {question}</h4>
            <p id="{unique_id}" style="font-size: 16px; color: #FFFFFF;">{answer}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ✅ Add a real Streamlit copy button (copies text)
        st.code(answer, language="text")  # This enables text selection & copying in a user-friendly way

# **Submit Button Logic**
if st.button("Submit"):
    if optional_question:
        st.info(f"Generating answer for: {optional_question}")

        response = openai.ChatCompletion.create(
            model=selected_model,
            messages=[{"role": "user", "content": optional_question}],
            max_tokens=800,
            temperature=0.1
        )

        answer = clean_answer(response.choices[0].message.content.strip())

        if not answer:
            answer = "⚠ No specific answer was found for this question."

        display_answer(optional_question, answer, "Single")

    elif uploaded_file and customer_name and column_location:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, engine="openpyxl")
            question_index = ord(column_location.strip().upper()) - ord('A')
            questions = df.iloc[:, question_index].dropna().tolist()

            if not questions:
                st.warning("⚠ No valid questions found in the selected column.")
                st.stop()

            for idx, question in enumerate(questions, 1):
                response = openai.ChatCompletion.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": question}],
                    max_tokens=800,
                    temperature=0.1
                )

                answer = clean_answer(response.choices[0].message.content.strip())

                display_answer(question, answer, idx)

        except Exception as e:
            st.error(f"Error processing file: {e}")


