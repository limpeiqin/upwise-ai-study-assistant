
import streamlit as st

st.set_page_config(
    page_title="Upwise",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Upwise")
st.subheader("Your Personal AI Learning Companion")

st.write(
    "Welcome to Upwise! Organize your study materials, "
    "summarize documents, generate quizzes, "
    "and ask questions about your learning resources."
)

st.divider()

st.subheader("✨ Your Study Tools")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📚 Study Library")
    st.write("Save and organize your study documents by subject.")

    st.markdown("### 📝 AI Summary")
    st.write("Turn lengthy documents into clear, concise summaries.")

    st.markdown("### 🗂️ AI Flashcards")
    st.write("Create flashcards to memorize important concepts and definitions.")

    st.markdown("### 🧠 AI Mind Map")
    st.write("Visualize key concepts and their connections from your study notes.")

with col2:
    st.markdown("### 💡 AI Quiz")
    st.write("Generate practice questions from your study materials.")

    st.markdown("### 💬 AI Study Chatbot")
    st.write("Ask questions about your documents and learning resources.")

    st.markdown("### 🗓️ AI Study Planner")
    st.write("Organize your revision schedule and plan your study sessions.")

st.divider()

st.info(
    "Choose a page from the navigation menu on the left "
    "to get started with Upwise."
)
