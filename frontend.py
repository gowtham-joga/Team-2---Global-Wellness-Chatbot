import streamlit as st
import requests
import os
import pandas as pd
from html import escape

# -------------------------
# Config & CSS loader
# -------------------------
st.set_page_config(page_title="Global Wellness Chatbot", layout="wide", page_icon="💬")
BACKEND_URL = "http://127.0.0.1:8000"

theme_base = st.get_option("theme.base")
if theme_base not in ("light", "dark"): theme_base = "light"
css_file = "style_dark.css" if theme_base == "dark" else "style_light.css"
if os.path.exists(css_file):
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning(f"⚠ CSS file '{css_file}' not found.")

# -------------------------
# State initialization
# -------------------------
## UPDATED: Includes all necessary state variables ##
for key in ['token', 'user_details', 'page', 'admin_page', 'lang', 'chat_history', 'feedback_in_progress']:
    if key not in st.session_state: st.session_state[key] = None if key != 'page' else 'auth'
if st.session_state.lang is None: st.session_state.lang = 'en'
if st.session_state.chat_history is None: st.session_state.chat_history = []
if st.session_state.user_details is None: st.session_state.user_details = {}

## NEW: Handles page routing from URL for password reset ##
if "page" in st.query_params and st.session_state.page == "auth":
    if st.query_params.get("page") == "reset-password":
        st.session_state.page = "reset_password"

# -------------------------
# Translations helper
# -------------------------
LANGUAGES = {
    "en": {"title": "Global Wellness Chatbot", "login": "Login", "register": "Register", "email": "Email", "password": "Password", "username": "Username", "chat": "Chat", "profile": "Profile", "logout": "Logout", "admin_panel": "Admin Panel", "ask": "Ask anything...", "thinking": "Thinking...", "welcome": "Welcome", "nav": "Navigation", "lang": "Language", "profile_header": "Your Profile", "update": "Update Profile", "updated": "Profile updated!", "reg_success": "Registration successful! Please login."},
    "hi": {"title": "ग्लोबल वेलनेस चैटबॉट", "login": "लॉगिन करें", "register": "रजिस्टर करें", "email": "ईमेल", "password": "पासवर्ड", "username": "यूजरनेम", "chat": "चैट", "profile": "प्रोफ़ाइल", "logout": "लॉग आउट", "admin_panel": "एडमिन पैनल", "ask": "कुछ भी पूछें...", "thinking": "सोच रहा है...", "welcome": "आपका स्वागत है", "nav": "नेविगेशन", "lang": "भाषा", "profile_header": "आपकी प्रोफ़ाइल", "update": "प्रोफ़ाइल अपडेट करें", "updated": "प्रोफ़ाइल अपडेट हो गई!", "reg_success": "पंजीकरण सफल! कृपया लॉगिन करें."}
}
def t(k): return LANGUAGES.get(st.session_state.lang, {}).get(k, k)

# -------------------------
# API helpers
# -------------------------
def get_auth_header(): return {"Authorization": f"Bearer {st.session_state.token}"}
def login_api(e, p): return requests.post(f"{BACKEND_URL}/users/login", data={"username": e, "password": p})
def get_user_api(): return requests.get(f"{BACKEND_URL}/users/me", headers=get_auth_header())
def post_message_api(msg, lang): return requests.post(f"{BACKEND_URL}/chat/", headers=get_auth_header(), json={"message": msg, "language": lang})
## FIX: Removed dummy password from update_user_api to match backend ##
def update_user_api(un, em, la): return requests.put(f"{BACKEND_URL}/users/me", headers=get_auth_header(), json={"username": un, "email": em, "language": la})
def register_api(un, em, pw): return requests.post(f"{BACKEND_URL}/users/register", json={"username": un, "email": em, "password": pw, "confirm_password": pw})
def post_feedback_api(data): return requests.post(f"{BACKEND_URL}/chat/feedback", headers=get_auth_header(), json=data)
def get_summary_stats_api(): return requests.get(f"{BACKEND_URL}/admin/summary-stats", headers=get_auth_header())
def get_feedback_summary_api(): return requests.get(f"{BACKEND_URL}/admin/feedback-summary", headers=get_auth_header())
def get_query_trends_api(): return requests.get(f"{BACKEND_URL}/admin/query-trends", headers=get_auth_header())
def get_usage_stats_api(): return requests.get(f"{BACKEND_URL}/admin/usage", headers=get_auth_header())
def get_intents_api(): return requests.get(f"{BACKEND_URL}/admin/intents", headers=get_auth_header())
def get_all_kb_api(search: str = "", intent: str = ""):
    return requests.get(f"{BACKEND_URL}/admin/kb", headers=get_auth_header(), params={"search": search, "intent": intent})
def add_kb_api(data): return requests.post(f"{BACKEND_URL}/admin/kb", headers=get_auth_header(), json=data)
def update_kb_api(kb_id, data): return requests.put(f"{BACKEND_URL}/admin/kb/{kb_id}", headers=get_auth_header(), json=data)
def delete_kb_api(kb_id): return requests.delete(f"{BACKEND_URL}/admin/kb/{kb_id}", headers=get_auth_header())
def get_feedback_api(): return requests.get(f"{BACKEND_URL}/admin/feedback", headers=get_auth_header())
def get_unanswered_questions_api(): return requests.get(f"{BACKEND_URL}/admin/unanswered-questions", headers=get_auth_header())
def forgot_password_api(email): return requests.post(f"{BACKEND_URL}/users/forgot-password", json={"email": email})
def reset_password_api(token, new_pass): return requests.post(f"{BACKEND_URL}/users/reset-password", json={"token": token, "new_password": new_pass, "confirm_new_password": new_pass})

# -------------------------
# Intent Emojis & UI Helpers
# -------------------------
INTENT_EMOJIS = {"greet": "👋", "goodbye": "👋", "chitchat": "💬", "ask_first_aid": "⛑️", "inform_symptom": "🤒", "ask_disease_info": "🩺", "ask_prevention": "🛡️", "emergency_help": "🚨", "ask_wellness_tips": "🌿", "ask_diet": "🥗", "ask_exercise": "💪", "ask_sleep": "😴", "ask_hygine": "🧼", "ask_mental_health": "🧠", "ask_productivity": "📈"}
def add_intent_emoji(text: str, intent: str) -> str:
    emoji = INTENT_EMOJIS.get(intent, "")
    safe = escape(text)
    return f"{emoji} {safe}" if emoji else safe
def render_user_message(text: str): st.markdown(f'<div class="user-message">{escape(text)}</div>', unsafe_allow_html=True)
def render_bot_message(text_html: str): st.markdown(f'<div class="bot-message">{text_html}</div>', unsafe_allow_html=True)

# -------------------------
# Pages
# -------------------------
def auth_page():
    st.title(t('title'))
    ## FIX: Added a non-empty label to the selectbox to remove terminal warning ##
    choice = st.selectbox("Login or Register", [t("login"), t("register")], label_visibility="collapsed")
    with st.form(key=f"auth_{choice}"):
        email = st.text_input(t("email"))
        password = st.text_input(t("password"), type="password")
        username = ""
        if choice == t("register"): username = st.text_input(t("username"))
        if st.form_submit_button(choice):
            if choice == t("login"):
                res = login_api(email, password)
                if res.status_code == 200:
                    st.session_state.token = res.json()['access_token']
                    me_res = get_user_api()
                    if me_res.status_code == 200:
                        st.session_state.user_details = me_res.json()
                        st.session_state.lang = st.session_state.user_details.get('language', 'en')
                    st.session_state.page = 'chat'; st.rerun()
                else: st.error("Login failed")
            else:
                res = register_api(username, email, password)
                if res.status_code == 201: st.success(t("reg_success"))
                else: st.error(f"Registration failed: {res.text}")
    
    ## NEW: Forgot Password Link ##
    if st.button("Forgot Password?"):
        st.session_state.page = "forgot_password"; st.rerun()

## UPDATED: chat_page with optional comment logic ##
def chat_page():
    st.header(t('title'))
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            render_user_message(message["content"])
        else:
            render_bot_message(message["content"])
            if message.get("feedback_submitted"):
                st.markdown("<div class='feedback-thanks'>Thanks for your feedback!</div>", unsafe_allow_html=True)
            elif st.session_state.feedback_in_progress and st.session_state.feedback_in_progress["index"] == i:
                feedback_data = st.session_state.feedback_in_progress
                with st.form(key=f"feedback_form_{i}"):
                    comment = st.text_input("Add an optional comment...", key=f"comment_{i}")
                    if st.form_submit_button("Submit Feedback"):
                        full_feedback_data = {"user_message": st.session_state.chat_history[i-1]['content'], "bot_response": message['raw_content'], "intent": message['intent'], "feedback": feedback_data["rating"], "comment": comment if comment else None}
                        post_feedback_api(full_feedback_data)
                        st.session_state.chat_history[i]['feedback_submitted'] = True
                        st.session_state.feedback_in_progress = None
                        st.rerun()
            else:
                cols = st.columns([1, 1, 10])
                with cols[0]:
                    if st.button("👍", key=f"up_{i}", width='stretch'):
                        st.session_state.feedback_in_progress = {"index": i, "rating": 1}; st.rerun()
                with cols[1]:
                    if st.button("👎", key=f"down_{i}", width='stretch'):
                        st.session_state.feedback_in_progress = {"index": i, "rating": 0}; st.rerun()

    if user_prompt := st.chat_input(t("ask")):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        render_user_message(user_prompt)
        with st.spinner(t("thinking")):
            res = post_message_api(user_prompt, st.session_state.lang)
            if res.status_code == 200:
                data = res.json()
                bot_text, intent = data.get("response", ""), data.get("intent", "") or ""
                formatted = add_intent_emoji(bot_text, intent).replace("\n", "<br>")
                st.session_state.chat_history.append({"role": "assistant", "content": formatted, "raw_content": bot_text, "intent": intent})
                st.rerun()
            else:
                st.error("Failed to get response.")

def profile_page():
    st.header(t('profile_header'))
    with st.form("profile_form"):
        username = st.text_input(t("username"), value=st.session_state.user_details.get('username', ''))
        email = st.text_input(t("email"), value=st.session_state.user_details.get('email', ''))
        new_lang_display = st.selectbox(t("lang"), ["English", "Hindi"], index=(0 if st.session_state.lang == "en" else 1))
        new_lang_code = "en" if new_lang_display == "English" else "hi"
        if st.form_submit_button(t("update")):
            res = update_user_api(username, email, new_lang_code)
            if res.status_code == 200:
                st.session_state.user_details = res.json()
                st.session_state.lang = new_lang_code
                st.success(t("updated")); st.rerun()
            else: st.error("Update failed")

## NEW PAGES: for password reset ##
def forgot_password_page():
    st.title("Forgot Password")
    with st.form("forgot_password_form"):
        email = st.text_input("Enter your email address")
        if st.form_submit_button("Request Password Reset"):
            res = forgot_password_api(email)
            if res.status_code == 200:
                st.success("If an account exists, a reset link will be sent to your email (or printed to the backend terminal).")
            else: st.error("An error occurred.")
    if st.button("← Back to Login"):
        st.session_state.page = "auth"; st.rerun()

def reset_password_page():
    st.title("Reset Your Password")
    token = st.query_params.get("token")
    if not token:
        st.error("No reset token found. Please use the link from your email.")
        if st.button("← Back to Login"):
            st.session_state.page = "auth"; st.rerun()
        return

    with st.form("reset_password_form"):
        new_password = st.text_input("Enter your new password", type="password")
        if st.form_submit_button("Set New Password"):
            res = reset_password_api(token, new_password)
            if res.status_code == 200:
                st.success("Password has been reset successfully! Please log in.")
                st.session_state.page = "auth"
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"Failed to reset password: {res.json().get('detail', 'Invalid or expired token.')}")

# Admin Pages
def admin_dashboard_page():
    st.markdown("<div class='admin-header'>Dashboard</div>", unsafe_allow_html=True)
    res = get_summary_stats_api()
    if res.status_code == 200:
        stats, fb_res = res.json(), get_feedback_summary_api()
        positive_fb = fb_res.json()['positive_feedback_percentage'] if fb_res.status_code == 200 else "N/A"
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Users", stats.get('total_users', 0)); c2.metric("Queries Handled", stats.get('queries_handled', 0)); c3.metric("Positive Feedback", f"{positive_fb}%")
    else: st.error("Could not load summary stats.")
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Query Trends (Last 7 Days)")
        res = get_query_trends_api()
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json()).rename(columns={'date': 'Date', 'queries': 'Queries'}); df['Date'] = pd.to_datetime(df['Date']); df = df.set_index('Date')
            st.line_chart(df)
        else: st.info("Not enough data for query trends.")
    with c2:
        st.subheader("Top Intents")
        res = get_usage_stats_api()
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json()).rename(columns={'intent': 'Intent', 'count': 'Count'}); df = df.set_index('Intent')
            st.bar_chart(df)
        else: st.info("No usage data available.")

def admin_kb_page():
    st.markdown("<div class='admin-header'>Knowledge Base Management</div>", unsafe_allow_html=True)
    with st.expander("➕ Add New KB Entry", expanded=False):
        with st.form("add_kb_form", clear_on_submit=True):
            intent, entity, response = st.text_input("Intent"), st.text_input("Entity (optional)"), st.text_area("Response Text")
            if st.form_submit_button("Add Entry"):
                data = {"intent": intent, "entity_value": entity if entity else None, "response_text": response}
                if add_kb_api(data).status_code == 200: st.success("Entry added!")
                else: st.error(f"Failed to add entry: {add_kb_api(data).text}")
    st.markdown("---")
    st.subheader("Search & Manage Entries")
    intents_res, intent_list = get_intents_api(), ["All"]
    if intents_res.status_code == 200: intent_list.extend(intents_res.json())
    c1, c2 = st.columns([0.7, 0.3])
    search_query = c1.text_input("Search entries by keyword", placeholder="e.g., fever, headache...")
    intent_filter = c2.selectbox("Filter by Intent", options=intent_list)
    selected_intent = intent_filter if intent_filter != "All" else ""
    res = get_all_kb_api(search=search_query, intent=selected_intent)
    if res.status_code == 200:
        kb_entries = res.json()
        st.info(f"Found {len(kb_entries)} matching entries.")
        for entry in kb_entries:
            with st.expander(f"**{entry['intent']}** | Entity: `{entry.get('entity_value') or 'None'}`"):
                with st.form(key=f"update_form_{entry['id']}"):
                    new_intent, new_entity, new_response = st.text_input("Intent", entry['intent']), st.text_input("Entity", entry.get('entity_value', '')), st.text_area("Response", entry['response_text'], height=150)
                    c1, c2 = st.columns([0.8, 0.2])
                    if c1.form_submit_button("Update"):
                        data = {"intent": new_intent, "entity_value": new_entity if new_entity else None, "response_text": new_response}
                        if update_kb_api(entry['id'], data).status_code == 200: st.success("Updated!"); st.rerun()
                        else: st.error(f"Update failed: {update_kb_api(entry['id'], data).text}")
                    if c2.form_submit_button("Delete"):
                        if delete_kb_api(entry['id']).status_code == 200: st.success("Deleted!"); st.rerun()
                        else: st.error("Delete failed.")
    else: st.error("Could not load Knowledge Base entries.")

def admin_feedback_page():
    st.markdown("<div class='admin-header'>User Feedback & Analytics</div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["User Feedback", "Unanswered Questions"])
    with tab1:
        st.subheader("User Feedback Responses")
        res = get_feedback_api()
        if res.status_code == 200:
            feedback_items = res.json()
            if not feedback_items: st.info("No user feedback submitted yet.")
            else:
                for item in feedback_items:
                    feedback_icon = "👍" if item.get('feedback') == 1 else "👎"
                    with st.expander(f"{feedback_icon} Feedback on intent: `{item.get('intent', 'N/A')}`"):
                        st.markdown(f"**User Message:**"); st.info(item.get('user_message'))
                        st.markdown(f"**Bot Response:**"); st.success(item.get('bot_response'))
                        if item.get('comment'): st.markdown(f"**Comment:** {item.get('comment')}")
        else: st.error("Could not load feedback.")
    with tab2:
        st.subheader("Unanswered Questions")
        res = get_unanswered_questions_api()
        if res.status_code == 200:
            questions = res.json()
            if not questions: st.info("No unanswered questions logged.")
            else: st.dataframe(pd.DataFrame(questions), use_container_width=True)
        else: st.error("Could not load unanswered questions.")

# -------------------------
# Main App Router
# -------------------------
if not st.session_state.token:
    ## UPDATED: Routing for password reset ##
    if st.session_state.page == 'forgot_password':
        forgot_password_page()
    elif st.session_state.page == 'reset_password':
        reset_password_page()
    else:
        auth_page()
else:
    with st.sidebar:
        st.markdown(f"<div class='welcome'>👋 {t('welcome')}, {st.session_state.user_details.get('username','')}</div>", unsafe_allow_html=True)
        if st.session_state.user_details.get('is_admin'): page_choice = st.selectbox(t("nav"), [t("chat"), t("profile"), t("admin_panel")])
        else: page_choice = st.selectbox(t("nav"), [t("chat"), t("profile")])
        if page_choice == t("chat"): st.session_state.page = 'chat'
        elif page_choice == t("profile"): st.session_state.page = 'profile'
        elif page_choice == t("admin_panel"): st.session_state.page = 'admin'
        if st.session_state.page == 'admin':
            st.markdown("---")
            st.markdown("<p style='font-weight: 600;'>Admin Menu</p>", unsafe_allow_html=True)
            admin_page_choice = st.radio("Admin Sections", ["Dashboard", "Knowledge Base", "Feedback"], label_visibility="collapsed")
            st.session_state.admin_page = admin_page_choice
        lang_map = {"English": "en", "Hindi": "hi"}
        current_lang_display = "English" if st.session_state.lang == "en" else "Hindi"
        lang_display = st.selectbox(t("lang"), list(lang_map.keys()), index=list(lang_map.keys()).index(current_lang_display))
        if (new_lang := lang_map[lang_display]) != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()
        ## FIX: Replaced use_container_width with width='stretch' ##
        if st.button(t('logout'), width='stretch'):
            st.session_state.clear()
            st.rerun()
    if st.session_state.page == 'chat': chat_page()
    elif st.session_state.page == 'profile': profile_page()
    elif st.session_state.page == 'admin':
        if st.session_state.admin_page == "Dashboard": admin_dashboard_page()
        elif st.session_state.admin_page == "Knowledge Base": admin_kb_page()
        elif st.session_state.admin_page == "Feedback": admin_feedback_page()