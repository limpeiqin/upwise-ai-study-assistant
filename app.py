
import streamlit as st
from pathlib import Path
from auth import show_auth_page
from supabase_client import supabase

st.set_page_config(
    page_title="Upwise",
    page_icon="📈",
    layout="wide"
)

# Upwise sidebar logo
logo_path = Path(__file__).parent / "assets" / "Upwise_Logo.png"

if logo_path.exists():
    st.sidebar.image(str(logo_path), width=220)

st.markdown("""
<style>
/* Sidebar background and spacing */
[data-testid="stSidebar"] {
    background: #171B2B;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1rem;
}

/* Sidebar section headings */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #A5B4FC;
}

/* Navigation links */
[data-testid="stSidebarNav"] a {
    border-radius: 10px;
    padding: 0.65rem 0.8rem;
    margin: 0.2rem 0;
    min-height: 44px;
    transition: background-color 0.2s ease;
}

/* Hover effect */
[data-testid="stSidebarNav"] a:hover {
    background: #2A3045;
}

/* Active page */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: #343B60;
    border-left: 3px solid #818CF8;
}

/* Navigation text */
[data-testid="stSidebarNav"] span {
    font-size: 1rem;
}

/* Sidebar divider */
[data-testid="stSidebar"] hr {
    border-color: #343A50;
}
</style>
""", unsafe_allow_html=True)

home = st.Page(
    "pages/1_Home.py",
    title="Home",
    icon="🏠",
    default=True
)

library = st.Page(
    "study_library.py",
    title="Study Library",
    icon="📚"
)

summary = st.Page(
    "pages/2_AI_Summary.py",
    title="AI Summary",
    icon="📝"
)

quiz = st.Page(
    "pages/3_AI_Quiz.py",
    title="AI Quiz",
    icon="🧠"
)

chatbot = st.Page(
    "pages/4_Study_Chatbot.py",
    title="Study Chatbot",
    icon="💬"
)

flashcards = st.Page(
    "pages/5_Flashcards.py",
    title="AI Flashcards",
    icon="🗂️"
)

planner = st.Page(
    "pages/6_AI_Study_Planner.py",
    title="AI Study Planner",
    icon="📅"
)

mind_map = st.Page(
    "pages/7_AI_Mind_Map.py",
    title="AI Mind Map",
    icon="🧠"
)

navigation = st.navigation(
    {
        "Main Menu": [home, library],
        "AI Study Tools": [
            summary,
            quiz,
            chatbot,
            flashcards,
            planner, 
            mind_map
        ]
    }
)

if "user" not in st.session_state:
    show_auth_page()
else:
    # Sign Out button in the sidebar
    st.sidebar.divider()
    st.sidebar.write("Signed in to Upwise")

    if st.sidebar.button("Sign Out", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.pop("user", None)
        st.session_state.pop("session", None)
        st.rerun()

    navigation.run()




