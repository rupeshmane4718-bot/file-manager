import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime

# ---------------- DATABASE SETUP ---------------- #
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")
conn.commit()

# ---------------- HELPER FUNCTIONS ---------------- #
def hash_password(password):
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    c.execute("INSERT INTO users (username, password) VALUES (?,?)", 
              (username, hash_password(password)))
    conn.commit()

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
              (username, hash_password(password)))
    return c.fetchone()

# ---------------- STREAMLIT UI ---------------- #
st.set_page_config(page_title="Secure File Manager", page_icon="🔒", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

menu = ["Login", "Signup"]
choice = st.sidebar.radio("Menu", menu)

# ---------------- LOGIN / SIGNUP ---------------- #
if not st.session_state.logged_in:
    if choice == "Signup":
        st.subheader("📝 Create New Account")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Signup"):
            try:
                create_user(new_user, new_pass)
                st.success("✅ Account created successfully! Please login.")
            except:
                st.error("⚠️ Username already exists!")

    elif choice == "Login":
        st.subheader("🔑 Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"✅ Welcome {username}!")
                st.rerun()   # ✅ updated for new Streamlit
            else:
                st.error("❌ Invalid username or password")

# ---------------- FILE MANAGER ---------------- #
else:
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()   # ✅ updated

    st.title("📂 Secure File Manager")

    # Create user folder
    user_folder = os.path.join("user_data", st.session_state.username)
    os.makedirs(user_folder, exist_ok=True)

    # File uploader
    uploaded_file = st.file_uploader("Upload Image/PDF", type=["png", "jpg", "jpeg", "pdf"])
    if uploaded_file:
        file_path = os.path.join(
            user_folder, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
        )
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ File saved: {uploaded_file.name}")

    # Show user’s files with icons
    st.subheader("📁 Your Saved Files")
    files = os.listdir(user_folder)

    if files:
        cols = st.columns(4)  # 4 files per row
        for index, file in enumerate(files):
            file_path = os.path.join(user_folder, file)
            col = cols[index % 4]  # distribute across columns
            with col:
                if file.endswith((".png", ".jpg", ".jpeg")):
                    st.image(file_path, caption=file, width=120)  # thumbnail
                    with open(file_path, "rb") as f:
                        st.download_button("📥 Open", f, file)
                elif file.endswith(".pdf"):
                    st.markdown(f"📄 **{file}**")
                    with open(file_path, "rb") as f:
                        st.download_button("📥 Open", f, file, "application/pdf")
    else:
        st.info("No files uploaded yet.")
