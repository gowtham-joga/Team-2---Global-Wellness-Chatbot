import os
import streamlit as st
import requests

# ---------- Config ----------
API_BASE_URL = "http://127.0.0.1:8000/users"

# ---------- CSS Styling ----------
st.markdown("""
    <style>
        body {
            background-color: #f4f6f9;
        }
        .main-title {
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        .success-msg {
            color: #27ae60;
            font-weight: 500;
        }
        .error-msg {
            color: #c0392b;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Title ----------
st.markdown("<div class='main-title'>Global Wellness Chatbot</div>", unsafe_allow_html=True)

# ---------- Tabs ----------
tabs = st.tabs(["Register", "Login", "Profile Update"])

# -------- Register Tab --------
with tabs[0]:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Register New User")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    age = st.number_input("Age", min_value=10, max_value=100, step=1)
    language = st.selectbox("Preferred Language", ["English", "Hindi"])
    
    if st.button("Register"):
        payload = {"username": username, "email": email, "password": password, "age": age, "language": language}
        try:
            res = requests.post(f"{API_BASE_URL}/register", json=payload)
            if res.status_code == 201:
                st.markdown("<p class='success-msg'>✅ Registration successful!</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p class='error-msg'>⚠️ {res.json()['detail']}</p>", unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<p class='error-msg'>⚠️ Error: {e}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------- Login Tab --------
with tabs[1]:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("User Login")
    login_email = st.text_input("Login Email")
    login_password = st.text_input("Login Password", type="password")
    
    if st.button("Login"):
        payload = {"email": login_email, "password": login_password}
        try:
            res = requests.post(f"{API_BASE_URL}/login", json=payload)
            if res.status_code == 200:
                st.session_state["token"] = res.json()["access_token"]
                st.markdown("<p class='success-msg'>✅ Login successful!</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p class='error-msg'>⚠️ {res.json()['detail']}</p>", unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<p class='error-msg'>⚠️ Error: {e}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------- Profile Update Tab --------
with tabs[2]:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Update Profile")
    if "token" not in st.session_state:
        st.warning("⚠️ Please login first to update your profile.")
    else:
        new_age = st.number_input("New Age", min_value=10, max_value=100, step=1)
        new_language = st.selectbox("New Preferred Language", ["English", "Hindi"])
        if st.button("Update Profile"):
            payload = {"age": new_age, "language": new_language}
            headers = {"Authorization": f"Bearer {st.session_state['token']}"}
            try:
                res = requests.put(f"{API_BASE_URL}/update", json=payload, headers=headers)
                if res.status_code == 200:
                    st.markdown("<p class='success-msg'>✅ Profile updated successfully!</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p class='error-msg'>⚠️ {res.json()['detail']}</p>", unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"<p class='error-msg'>⚠️ Error: {e}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
