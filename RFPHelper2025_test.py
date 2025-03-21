import streamlit as st
import pandas as pd
import openai
import re
from io import BytesIO
import os
import sqlite3
from sqlite3 import Error

# =============================================================================
# DATABASE HELPER FUNCTIONS (Persistent Storage for Users)
# =============================================================================
DB_FILE = "users.db"

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
    except Error as e:
        st.error(f"Error connecting to database: {e}")
    return conn

def create_table(conn):
    """Create the users table if it doesn't exist."""
    try:
        sql_create_users_table = """ 
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            password TEXT NOT NULL
        );
        """
        cur = conn.cursor()
        cur.execute(sql_create_users_table)
        conn.commit()
    except Error as e:
        st.error(f"Error creating table: {e}")

def add_user(conn, email, first_name, last_name, password):
    """Add a new user to the users table."""
    try:
        sql = """INSERT INTO users(email, first_name, last_name, password)
                 VALUES(?,?,?,?)"""
        cur = conn.cursor()
        cur.execute(sql, (email, first_name, last_name, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Email already registered.
        return False
    except Error as e:
        st.error(f"Error adding user: {e}")
        return False

def authenticate_user(conn, email, password):
    """Check if the provided email and password match a user."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        row = cur.fetchone()
        return row is not None
    except Error as e:
        st.error(f"Error during authentication: {e}")
        return False

def get_user(conn, email):
    """Retrieve user data for the given email."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        return cur.fetchone()
    except Error as e:
        st.error(f"Error retrieving user: {e}")
        return None

# =============================================================================
# SETUP DATABASE
# =============================================================================
conn = create_connection(DB_FILE)
create_table(conn)

# =============================================================================
# SET PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Skyhigh Security",
    page_icon="🔒",
    layout="wide"
)

# =============================================================================
# BACKGROUND IMAGE FUNCTION
# =============================================================================
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

# Set the background image for the auth page.
set_background("https://raw.githubusercontent.com/lmarecha78/RFP_AI_tool/main/skyhigh_bg.png")

# =============================================================================
# SESSION STATE FOR AUTHENTICATION
# =============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# =============================================================================
# AUTHENTICATION PAGE
# =============================================================================
if not st.session_state.authenticated:
    st.title("Authentication")
    auth_mode = st.radio("Select Mode", ["Login", "Register"], key="auth_mode")
    
    if auth_mode == "Register":
        st.subheader("Register")
        with st.form("registration_form"):
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Corporate Email (must be @skyhighsecurity.com)")
            password = st.text_input("Password", type="password")
            reg_submitted = st.form_submit_button("Register")
            if reg_submitted:
                if not email.lower().endswith("@skyhighsecurity.com"):
                    st.error("Please provide a corporate email address ending with @skyhighsecurity.com.")
                elif not (first_name and last_name and password):
                    st.error("Please fill in all the fields.")
                else:
                    success = add_user(conn, email, first_name, last_name, password)
                    if success:
                        st.success("Registration successful! Please switch to the Login tab.")
                    else:
                        st.error("This email is already registered. Please login.")
    else:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")
            if login_submitted:
                if authenticate_user(conn, email, password):
                    st.session_state.authenticated = True
                    st.session_state.current_user = email
                    st.success("Login successful!")
                    st.rerun()  # Refresh the app to show the main content.
                else:
                    st.error("Invalid email or password.")
    
    st.stop()

# =============================================================================
# MAIN APP PAGE (AFTER AUTHENTICATION)
# =============================================================================

# Re-apply the background image for the main app.
set_background("https://raw.githubusercontent.com/lmarecha78/RFP_AI_tool/main/skyhigh_bg.png")

# Add a "Log off" button at the top-right (or where preferred)
if st.button("Log off", key="logoff_button"):
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()

user = get_user(conn, st.session_state.current_user)
st.title("Welcome to the Skyhigh Security App")
if user:
    st.write(f"Hello, {user[1]} {user[2]}!")
else:
    st.write("User data not found.")

# =============================================================================
# THE RFI/RFP TOOL CODE (WITH DYNAMIC UI AND DISABLE LOGIC)
# =============================================================================

# ------------------------------------------------------------------------------
# INITIALIZE/DYNAMIC UI VERSION FOR WIDGET KEYS
# ------------------------------------------------------------------------------
if "ui_version" not in st.session_state:
    st.session_state.ui_version = 0

def restart_ui():
    st.session_state.ui_version += 1

# ------------------------------------------------------------------------------
# RFI/RFP TOOL HEADER
# ------------------------------------------------------------------------------
st.markdown("---")
st.header("Skyhigh Security - RFI/RFP AI Tool")

# ------------------------------------------------------------------------------
# RESTART BUTTON (using dynamic ui_version)
# ------------------------------------------------------------------------------
st.button("🔄 Restart", key=f"restart_button_{st.session_state.ui_version}", on_click=restart_ui)

# ------------------------------------------------------------------------------
# READ CURRENT VALUES FROM SESSION STATE (for disable logic)
# ------------------------------------------------------------------------------
customer_name_val = st.session_state.get(f"customer_name_{st.session_state.ui_version}", "").strip()
uploaded_file_val = st.session_state.get(f"uploaded_file_{st.session_state.ui_version}", None)
column_location_val = st.session_state.get(f"column_location_{st.session_state.ui_version}", "").strip()
unique_question_val = st.session_state.get(f"unique_question_{st.session_state.ui_version}", "").strip()

# Determine disabling logic:
disable_unique = bool(customer_name_val or uploaded_file_val or column_location_val)
disable_multi = bool(unique_question_val)

# ------------------------------------------------------------------------------
# USER INPUT FIELDS (with dynamic keys)
# ------------------------------------------------------------------------------
customer_name = st.text_input(
    "Customer Name",
    key=f"customer_name_{st.session_state.ui_version}",
    disabled=disable_multi
)

uploaded_file = st.file_uploader(
    "Upload a CSV or XLS file",
    type=["csv", "xls", "xlsx"],
    key=f"uploaded_file_{st.session_state.ui_version}",
    disabled=disable_multi
)

column_location = st.text_input(
    "Specify the location of the questions (e.g., B for column B)",
    key=f"column_location_{st.session_state.ui_version}",
    disabled=disable_multi
)

unique_question = st.text_input(
    "Extra/Optional: You can ask a unique question here",
    key=f"unique_question_{st.session_state.ui_version}",
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
    """Remove markdown bold formatting."""
    return re.sub(r'\*\*(.*?)\*\*', r'\1', answer).strip()

# ------------------------------------------------------------------------------
# SUBMIT BUTTON LOGIC
# ------------------------------------------------------------------------------
if st.button("Submit", key=f"submit_button_{st.session_state.ui_version}"):
    responses = []

    # CASE 1: Unique question approach
    if unique_question:
        questions = [unique_question]
    # CASE 2: Multi-question approach (requires all three fields)
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

    if uploaded_file and len(responses) == len(questions):
        df["Answers"] = pd.Series(responses)
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        st.download_button("📥 Download Responses", data=output, file_name="RFP_Responses.xlsx")


